"""Celery tasks for async processing: transcription, document extraction, metrics, notifications."""

import asyncio
import logging
import mimetypes
import os
import tempfile
import uuid
from datetime import datetime, date, time, timedelta, timezone

from app.workers.celery_app import celery

logger = logging.getLogger("empireo.worker")


# ---------------------------------------------------------------------------
# Helper: download a file from a URL to a temp path (sync, uses httpx)
# ---------------------------------------------------------------------------
def _download_url_to_tempfile(url: str, suffix: str = "") -> str:
    """Download a URL to a temporary file and return the file path."""
    import httpx

    with httpx.Client(timeout=120, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(resp.content)
        tmp.close()
        return tmp.name


def _download_s3_to_tempfile(file_key: str, suffix: str = "") -> str:
    """Download a file from S3 to a temporary file and return the file path."""
    from app.core.s3_service import get_s3_client
    from app.config import settings

    client = get_s3_client()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    client.download_fileobj(
        Bucket=settings.AWS_S3_BUCKET,
        Key=file_key,
        Fileobj=tmp,
    )
    tmp.close()
    return tmp.name


def _extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file. Uses PyPDF2 if available, falls back to basic reading."""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n\n".join(pages_text)
    except ImportError:
        logger.warning("PyPDF2 not installed, attempting pdfminer fallback")
        try:
            from pdfminer.high_level import extract_text

            return extract_text(file_path)
        except ImportError:
            logger.error("No PDF library available (PyPDF2 or pdfminer). Cannot extract text.")
            raise RuntimeError("No PDF extraction library available. Install PyPDF2 or pdfminer.six.")


def _extract_text_from_file(file_path: str, mime_type: str | None = None) -> str:
    """Extract text from a file based on its mime type."""
    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"

    if mime_type == "application/pdf" or file_path.lower().endswith(".pdf"):
        return _extract_text_from_pdf(file_path)
    elif mime_type.startswith("text/") or mime_type in (
        "application/json",
        "application/xml",
        "application/csv",
    ):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    else:
        # Try reading as text as a fallback
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            raise RuntimeError(f"Cannot extract text from mime type: {mime_type}")


# ---------------------------------------------------------------------------
# Task: send_notification (EXISTING - kept as-is)
# ---------------------------------------------------------------------------
@celery.task(name="send_notification", bind=True, max_retries=3)
def send_notification(self, user_id: str, title: str, message: str, notification_type: str = "general"):
    """Send a notification to a user (create DB record + FCM push).

    1. Creates an eb_notifications DB record
    2. Looks up user FCM tokens and sends push via FCM HTTP v1 API
    """
    try:
        from app.database import sync_session_factory
        from app.modules.notifications.models import Notification

        with sync_session_factory() as db:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
            )
            db.add(notification)
            db.commit()
            logger.info("Notification record created for user %s: %s", user_id, title)

        # Dispatch FCM push as a separate task to avoid blocking
        send_fcm_push.delay(user_id, title, message, {"type": notification_type})
        return {"user_id": user_id, "title": title, "status": "sent"}
    except Exception as exc:
        logger.error("Failed to send notification: %s", exc)
        raise self.retry(exc=exc, countdown=30)


# ---------------------------------------------------------------------------
# Task: send_fcm_push — mirrors Supabase Edge Function `Notification` (v18)
# ---------------------------------------------------------------------------
@celery.task(name="send_fcm_push", bind=True, max_retries=3)
def send_fcm_push(self, user_id: str, title: str, body: str, data: dict | None = None):
    """Send FCM push notification to all devices of a user.

    Mirrors the Supabase Edge Function `Notification` which:
    1. Gets Google OAuth2 access token via service account
    2. Looks up FCM tokens for the user
    3. Sends push via FCM HTTP v1 API
    """
    try:
        from app.core.fcm_service import send_push_notification, _get_google_access_token, _get_project_id
        from app.config import settings

        if not settings.GOOGLE_SERVICE_ACCOUNT_KEY:
            logger.info("FCM not configured, skipping push for user %s", user_id)
            return {"user_id": user_id, "status": "skipped", "reason": "fcm_not_configured"}

        # Look up FCM tokens synchronously
        from app.database import sync_session_factory
        from app.modules.push_tokens.models import UserFCMToken, UserPushToken
        from sqlalchemy import select

        tokens = set()
        with sync_session_factory() as db:
            push_result = db.execute(
                select(UserPushToken.fcm_token).where(UserPushToken.user_id == user_id)
            )
            for row in push_result.all():
                if row[0]:
                    tokens.add(row[0])

            fcm_result = db.execute(
                select(UserFCMToken.fcm_token).where(UserFCMToken.user_id == user_id)
            )
            for row in fcm_result.all():
                if row[0]:
                    tokens.add(row[0])

        if not tokens:
            logger.info("No FCM tokens for user %s", user_id)
            return {"user_id": user_id, "status": "no_tokens"}

        # Send to all devices
        results = []
        for token in tokens:
            result = asyncio.run(send_push_notification(token, title, body, data))
            results.append(result)

        sent = sum(1 for r in results if r.get("status") == "sent")
        logger.info("FCM push sent to %d/%d devices for user %s", sent, len(tokens), user_id)
        return {"user_id": user_id, "status": "sent", "devices_total": len(tokens), "devices_sent": sent}

    except Exception as exc:
        logger.error("FCM push failed for user %s: %s", user_id, exc)
        raise self.retry(exc=exc, countdown=30)


# ---------------------------------------------------------------------------
# Task: transcribe_call
# ---------------------------------------------------------------------------
@celery.task(name="transcribe_call", bind=True, max_retries=3)
def transcribe_call(self, call_analysis_id: str):
    """Transcribe a call recording and run quality analysis.

    Steps:
    1. Fetch CallAnalysis record and validate recording_url exists
    2. Download audio from recording_url via httpx to a temp file
    3. Use openai_service.transcribe_audio to get transcription
    4. Use openai_service.analyze_call to get quality scores
    5. Store all results back in the CallAnalysis record
    """
    logger.info("Transcribing call analysis %s", call_analysis_id)
    tmp_path = None
    try:
        from app.database import sync_session_factory
        from app.modules.employee_automation.models import CallAnalysis
        from app.core.openai_service import transcribe_audio, analyze_call
        from sqlalchemy import select

        with sync_session_factory() as db:
            result = db.execute(select(CallAnalysis).where(CallAnalysis.id == call_analysis_id))
            analysis = result.scalar_one_or_none()
            if not analysis:
                logger.warning("Call analysis %s not found", call_analysis_id)
                return {"call_analysis_id": call_analysis_id, "status": "not_found"}

            if not analysis.recording_url:
                analysis.transcription_status = "failed"
                analysis.transcription = None
                db.commit()
                return {"call_analysis_id": call_analysis_id, "status": "no_recording"}

            # Mark as processing
            analysis.transcription_status = "processing"
            db.commit()

            # Step 1: Download audio from recording_url
            recording_url = analysis.recording_url
            # Determine a reasonable suffix from the URL
            url_path = recording_url.split("?")[0]
            suffix = ""
            for ext in (".mp3", ".wav", ".ogg", ".m4a", ".webm", ".mp4", ".flac"):
                if url_path.lower().endswith(ext):
                    suffix = ext
                    break
            if not suffix:
                suffix = ".mp3"  # Default assumption for call recordings

            try:
                tmp_path = _download_url_to_tempfile(recording_url, suffix=suffix)
            except Exception as download_err:
                logger.error("Failed to download recording for %s: %s", call_analysis_id, download_err)
                analysis.transcription_status = "failed"
                analysis.summary = f"Download failed: {str(download_err)[:500]}"
                db.commit()
                raise

            # Step 2: Transcribe audio via OpenAI Whisper
            try:
                transcription_result = asyncio.run(transcribe_audio(tmp_path))
            except Exception as transcribe_err:
                logger.error("Transcription failed for %s: %s", call_analysis_id, transcribe_err)
                analysis.transcription_status = "failed"
                analysis.summary = f"Transcription failed: {str(transcribe_err)[:500]}"
                db.commit()
                raise

            transcription_text = transcription_result.get("text", "")
            analysis.transcription = transcription_text
            analysis.transcription_model = "whisper-1"
            analysis.language_detected = transcription_result.get("language")
            if transcription_result.get("duration"):
                analysis.duration_seconds = int(transcription_result["duration"])

            # Step 3: Analyze the transcription for quality scores
            if transcription_text and len(transcription_text.strip()) > 10:
                try:
                    analysis_result = asyncio.run(analyze_call(transcription_text))
                except Exception as analyze_err:
                    logger.warning("Call analysis failed for %s: %s", call_analysis_id, analyze_err)
                    # Transcription succeeded but analysis failed - still mark as completed
                    analysis.transcription_status = "completed"
                    analysis.analyzed_at = datetime.now(timezone.utc)
                    analysis.summary = f"Transcription OK, analysis failed: {str(analyze_err)[:200]}"
                    db.commit()
                    return {
                        "call_analysis_id": call_analysis_id,
                        "status": "partial",
                        "transcription": "ok",
                        "analysis": "failed",
                    }

                # Populate analysis fields
                analysis.sentiment_score = analysis_result.get("sentiment_score")
                analysis.quality_score = analysis_result.get("quality_score")
                analysis.professionalism_score = analysis_result.get("professionalism_score")
                analysis.resolution_score = analysis_result.get("resolution_score")
                analysis.summary = analysis_result.get("summary")
                analysis.topics = analysis_result.get("topics", [])
                analysis.action_items = analysis_result.get("action_items", [])
                analysis.flags = analysis_result.get("flags", [])
                analysis.key_phrases = analysis_result.get("key_phrases", [])
                analysis.caller_intent = analysis_result.get("caller_intent")
                analysis.outcome = analysis_result.get("outcome")
                analysis.ai_model_used = analysis_result.get("ai_model_used", "gpt-4o-mini")
                analysis.ai_tokens_used = analysis_result.get("ai_tokens_used", 0)
            else:
                analysis.summary = "Transcription produced insufficient text for analysis."

            analysis.transcription_status = "completed"
            analysis.analyzed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info("Call analysis %s completed successfully", call_analysis_id)
            return {"call_analysis_id": call_analysis_id, "status": "completed"}

    except Exception as exc:
        logger.error("Failed to transcribe call %s: %s", call_analysis_id, exc)
        # Mark as failed in DB if possible
        try:
            from app.database import sync_session_factory as sf
            from app.modules.employee_automation.models import CallAnalysis as CA
            from sqlalchemy import update as upd

            with sf() as db2:
                db2.execute(
                    upd(CA).where(CA.id == call_analysis_id)
                    .values(transcription_status="failed")
                )
                db2.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Task: process_file_ingestion
# ---------------------------------------------------------------------------
@celery.task(name="process_file_ingestion", bind=True, max_retries=3)
def process_file_ingestion(self, ingestion_id: str):
    """Process a file ingestion: download from S3, detect type, extract data, store results.

    Steps:
    1. Fetch FileIngestion record
    2. Download file from S3 via file_key
    3. Detect mime type and route accordingly:
       - Audio files -> dispatch transcribe_call task
       - PDF/text files -> extract text, run extract_document_data via OpenAI
    4. Store extracted_data and update processing status
    """
    logger.info("Processing file ingestion %s", ingestion_id)
    tmp_path = None
    try:
        from app.database import sync_session_factory
        from app.modules.employee_automation.models import FileIngestion, CallAnalysis
        from app.core.openai_service import extract_document_data
        from sqlalchemy import select

        with sync_session_factory() as db:
            result = db.execute(select(FileIngestion).where(FileIngestion.id == ingestion_id))
            ingestion = result.scalar_one_or_none()
            if not ingestion:
                logger.warning("File ingestion %s not found", ingestion_id)
                return {"ingestion_id": ingestion_id, "status": "not_found"}

            # Mark as processing
            ingestion.processing_status = "processing"
            ingestion.processing_started_at = datetime.now(timezone.utc)
            db.commit()

            file_key = ingestion.file_key
            file_name = ingestion.file_name or ""
            mime_type = ingestion.mime_type

            # Determine mime type if not set
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(file_name)
                mime_type = mime_type or "application/octet-stream"
                ingestion.mime_type = mime_type
                db.commit()

            # Determine file extension for temp file
            ext = ""
            if "." in file_name:
                ext = "." + file_name.rsplit(".", 1)[-1]

            # Download from S3
            try:
                tmp_path = _download_s3_to_tempfile(file_key, suffix=ext)
            except Exception as download_err:
                logger.error("Failed to download S3 file for ingestion %s: %s", ingestion_id, download_err)
                ingestion.processing_status = "failed"
                ingestion.processing_error = f"S3 download failed: {str(download_err)[:1000]}"
                ingestion.processing_completed_at = datetime.now(timezone.utc)
                db.commit()
                raise

            # Route by mime type
            is_audio = mime_type.startswith("audio/") or ext.lower() in (
                ".mp3", ".wav", ".ogg", ".m4a", ".webm", ".flac", ".aac",
            )

            if is_audio:
                # For audio files, create a CallAnalysis record and dispatch transcription
                logger.info("File ingestion %s is audio, dispatching transcribe_call", ingestion_id)
                call_analysis = CallAnalysis(
                    id=uuid.uuid4(),
                    employee_id=ingestion.employee_id,
                    recording_url=None,  # We have the S3 file, not a URL
                    transcription_status="pending",
                    file_ingestion_id=ingestion.id,
                )
                db.add(call_analysis)
                db.commit()
                call_analysis_id = str(call_analysis.id)

                # For audio ingestion, we transcribe directly here since we have the temp file
                from app.core.openai_service import transcribe_audio, analyze_call

                try:
                    transcription_result = asyncio.run(transcribe_audio(tmp_path))
                except Exception as transcribe_err:
                    logger.error("Audio transcription failed for ingestion %s: %s", ingestion_id, transcribe_err)
                    call_analysis.transcription_status = "failed"
                    ingestion.processing_status = "failed"
                    ingestion.processing_error = f"Transcription failed: {str(transcribe_err)[:1000]}"
                    ingestion.processing_completed_at = datetime.now(timezone.utc)
                    db.commit()
                    raise

                transcription_text = transcription_result.get("text", "")
                call_analysis.transcription = transcription_text
                call_analysis.transcription_model = "whisper-1"
                call_analysis.language_detected = transcription_result.get("language")
                if transcription_result.get("duration"):
                    call_analysis.duration_seconds = int(transcription_result["duration"])

                # Analyze the transcription
                analysis_data = {}
                if transcription_text and len(transcription_text.strip()) > 10:
                    try:
                        analysis_data = asyncio.run(analyze_call(transcription_text))
                        call_analysis.sentiment_score = analysis_data.get("sentiment_score")
                        call_analysis.quality_score = analysis_data.get("quality_score")
                        call_analysis.professionalism_score = analysis_data.get("professionalism_score")
                        call_analysis.resolution_score = analysis_data.get("resolution_score")
                        call_analysis.summary = analysis_data.get("summary")
                        call_analysis.topics = analysis_data.get("topics", [])
                        call_analysis.action_items = analysis_data.get("action_items", [])
                        call_analysis.flags = analysis_data.get("flags", [])
                        call_analysis.key_phrases = analysis_data.get("key_phrases", [])
                        call_analysis.caller_intent = analysis_data.get("caller_intent")
                        call_analysis.outcome = analysis_data.get("outcome")
                        call_analysis.ai_model_used = analysis_data.get("ai_model_used", "gpt-4o-mini")
                        call_analysis.ai_tokens_used = analysis_data.get("ai_tokens_used", 0)
                    except Exception as analyze_err:
                        logger.warning("Call analysis failed for ingestion %s: %s", ingestion_id, analyze_err)

                call_analysis.transcription_status = "completed"
                call_analysis.analyzed_at = datetime.now(timezone.utc)

                # Store results in FileIngestion
                ingestion.extracted_data = {
                    "type": "audio_transcription",
                    "transcription": transcription_text[:5000],  # Truncate for JSONB
                    "language": transcription_result.get("language"),
                    "duration": transcription_result.get("duration"),
                    "call_analysis_id": call_analysis_id,
                    "sentiment_score": analysis_data.get("sentiment_score"),
                    "quality_score": analysis_data.get("quality_score"),
                    "summary": analysis_data.get("summary"),
                }
                ingestion.ai_model_used = "whisper-1 + gpt-4o-mini"
                ingestion.ai_tokens_used = analysis_data.get("ai_tokens_used", 0)

            else:
                # Text/PDF/other document files - extract text and run AI extraction
                logger.info("File ingestion %s is document (mime: %s), extracting text", ingestion_id, mime_type)

                try:
                    text_content = _extract_text_from_file(tmp_path, mime_type)
                except Exception as extract_err:
                    logger.error("Text extraction failed for ingestion %s: %s", ingestion_id, extract_err)
                    ingestion.processing_status = "failed"
                    ingestion.processing_error = f"Text extraction failed: {str(extract_err)[:1000]}"
                    ingestion.processing_completed_at = datetime.now(timezone.utc)
                    db.commit()
                    raise

                if not text_content or len(text_content.strip()) < 5:
                    ingestion.extracted_data = {
                        "type": "document",
                        "error": "No meaningful text content extracted",
                        "raw_length": len(text_content) if text_content else 0,
                    }
                    ingestion.processing_status = "completed"
                    ingestion.processing_completed_at = datetime.now(timezone.utc)
                    db.commit()
                    logger.info("File ingestion %s completed (no text to analyze)", ingestion_id)
                    return {"ingestion_id": ingestion_id, "status": "completed", "detail": "no_text"}

                # Determine document type from entity_type or file name
                doc_type = ingestion.entity_type or "general"

                # Run AI extraction - truncate text to avoid token limits
                max_chars = 30000  # ~7500 tokens
                truncated_text = text_content[:max_chars]

                try:
                    extraction_result = asyncio.run(
                        extract_document_data(truncated_text, doc_type)
                    )
                except Exception as ai_err:
                    logger.warning("AI extraction failed for ingestion %s: %s", ingestion_id, ai_err)
                    # Still save the raw text extraction
                    ingestion.extracted_data = {
                        "type": "document",
                        "raw_text_preview": text_content[:2000],
                        "raw_text_length": len(text_content),
                        "ai_extraction_error": str(ai_err)[:500],
                    }
                    ingestion.processing_status = "completed"
                    ingestion.processing_completed_at = datetime.now(timezone.utc)
                    db.commit()
                    return {"ingestion_id": ingestion_id, "status": "completed", "detail": "ai_failed"}

                ingestion.extracted_data = {
                    "type": "document",
                    "raw_text_length": len(text_content),
                    "ai_extraction": extraction_result,
                }
                ingestion.ai_model_used = extraction_result.get("ai_model_used", "gpt-4o-mini")
                ingestion.ai_tokens_used = extraction_result.get("ai_tokens_used", 0)

            # Mark as completed
            ingestion.processing_status = "completed"
            ingestion.processing_completed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info("File ingestion %s processed successfully", ingestion_id)
            return {"ingestion_id": ingestion_id, "status": "completed"}

    except Exception as exc:
        logger.error("Failed to process ingestion %s: %s", ingestion_id, exc)
        try:
            from app.database import sync_session_factory as sf
            from app.modules.employee_automation.models import FileIngestion as FI
            from sqlalchemy import update as upd

            with sf() as db2:
                db2.execute(
                    upd(FI).where(FI.id == ingestion_id)
                    .values(
                        processing_status="failed",
                        processing_error=str(exc)[:2000],
                        processing_completed_at=datetime.now(timezone.utc),
                    )
                )
                db2.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Task: compute_employee_metrics
# ---------------------------------------------------------------------------
@celery.task(name="compute_employee_metrics", bind=True, max_retries=2)
def compute_employee_metrics(self, employee_id: str, period_type: str = "daily"):
    """Compute aggregated metrics for an employee over a given period.

    Queries: call_events (via profiles.callerId), eb_cases, eb_tasks, attendance.
    Aggregates counts, durations, and averages into an EmployeeMetric record.
    """
    logger.info("Computing %s metrics for employee %s", period_type, employee_id)
    try:
        from app.database import sync_session_factory
        from app.modules.employee_automation.models import EmployeeMetric, CallAnalysis
        from app.modules.users.models import User
        from app.modules.profiles.models import Profile
        from app.modules.call_events.models import CallEvent
        from app.modules.cases.models import Case
        from app.modules.tasks.models import Task
        from app.modules.attendance.models import Attendance
        from app.modules.documents.models import Document
        from sqlalchemy import select, func, and_, or_, cast, Date, case as sql_case

        with sync_session_factory() as db:
            # Fetch the user
            user_result = db.execute(select(User).where(User.id == employee_id))
            user = user_result.scalar_one_or_none()
            if not user:
                logger.warning("Employee %s not found", employee_id)
                return {"employee_id": employee_id, "status": "not_found"}

            # Determine the period
            now = datetime.now(timezone.utc)
            today = now.date()
            if period_type == "daily":
                period_start = today
                period_end = today
            elif period_type == "weekly":
                # Start of the current week (Monday)
                period_start = today - timedelta(days=today.weekday())
                period_end = period_start + timedelta(days=6)
            elif period_type == "monthly":
                period_start = today.replace(day=1)
                # Last day of month
                if today.month == 12:
                    period_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    period_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            else:
                period_start = today
                period_end = today

            period_start_dt = datetime.combine(period_start, time.min).replace(tzinfo=timezone.utc)
            period_end_dt = datetime.combine(period_end, time.max).replace(tzinfo=timezone.utc)

            # -------------------------------------------------------------------
            # 1. Call metrics - match via profiles.callerId or agent_phone_norm
            # -------------------------------------------------------------------
            # Find the user's profile to get callerId for matching call_events
            caller_id = user.caller_id
            agent_phone = None

            # Also try to match via legacy profile
            if user.legacy_supabase_id:
                profile_result = db.execute(
                    select(Profile).where(Profile.id == user.legacy_supabase_id)
                )
                profile = profile_result.scalar_one_or_none()
                if profile:
                    caller_id = caller_id or profile.callerId
                    if profile.phone:
                        agent_phone = str(profile.phone)

            calls_made = 0
            calls_received = 0
            calls_missed = 0
            total_call_duration_secs = 0
            call_count_with_duration = 0

            if caller_id or agent_phone:
                # Build agent matching condition
                agent_conditions = []
                if caller_id:
                    agent_conditions.append(CallEvent.agent_number == caller_id)
                    agent_conditions.append(CallEvent.callerid == caller_id)
                if agent_phone:
                    agent_conditions.append(CallEvent.agent_phone_norm == agent_phone)

                agent_filter = or_(*agent_conditions)

                # Outgoing calls (event_type like 'dial' or agent is caller)
                outgoing_q = db.execute(
                    select(func.count()).select_from(CallEvent).where(
                        and_(
                            agent_filter,
                            CallEvent.created_at >= period_start_dt,
                            CallEvent.created_at <= period_end_dt,
                            CallEvent.event_type.in_(["Dial", "dial", "DIAL", "CDR"]),
                        )
                    )
                )
                calls_made = outgoing_q.scalar() or 0

                # Incoming calls
                incoming_q = db.execute(
                    select(func.count()).select_from(CallEvent).where(
                        and_(
                            agent_filter,
                            CallEvent.created_at >= period_start_dt,
                            CallEvent.created_at <= period_end_dt,
                            CallEvent.event_type.in_(["Incoming", "incoming", "INCOMING"]),
                        )
                    )
                )
                calls_received = incoming_q.scalar() or 0

                # Missed calls
                missed_q = db.execute(
                    select(func.count()).select_from(CallEvent).where(
                        and_(
                            agent_filter,
                            CallEvent.created_at >= period_start_dt,
                            CallEvent.created_at <= period_end_dt,
                            or_(
                                CallEvent.call_status.in_(["missed", "no-answer", "busy"]),
                                CallEvent.event_type.in_(["Missed", "missed", "MISSED"]),
                            ),
                        )
                    )
                )
                calls_missed = missed_q.scalar() or 0

                # Total call duration
                duration_q = db.execute(
                    select(
                        func.coalesce(func.sum(CallEvent.conversation_duration), 0),
                        func.count(),
                    ).select_from(CallEvent).where(
                        and_(
                            agent_filter,
                            CallEvent.created_at >= period_start_dt,
                            CallEvent.created_at <= period_end_dt,
                            CallEvent.conversation_duration.isnot(None),
                            CallEvent.conversation_duration > 0,
                        )
                    )
                )
                duration_row = duration_q.one()
                total_call_duration_secs = duration_row[0] or 0
                call_count_with_duration = duration_row[1] or 0

            total_call_duration_mins = round(total_call_duration_secs / 60.0, 2) if total_call_duration_secs else 0
            avg_call_duration_mins = (
                round(total_call_duration_mins / call_count_with_duration, 2)
                if call_count_with_duration > 0
                else 0
            )

            # -------------------------------------------------------------------
            # 2. Call quality scores from CallAnalysis
            # -------------------------------------------------------------------
            quality_q = db.execute(
                select(
                    func.avg(CallAnalysis.quality_score),
                    func.avg(CallAnalysis.sentiment_score),
                ).select_from(CallAnalysis).where(
                    and_(
                        CallAnalysis.employee_id == employee_id,
                        CallAnalysis.transcription_status == "completed",
                        CallAnalysis.analyzed_at >= period_start_dt,
                        CallAnalysis.analyzed_at <= period_end_dt,
                    )
                )
            )
            quality_row = quality_q.one()
            avg_call_quality = round(float(quality_row[0]), 2) if quality_row[0] else None
            avg_call_sentiment = round(float(quality_row[1]), 2) if quality_row[1] else None

            # -------------------------------------------------------------------
            # 3. Case metrics
            # -------------------------------------------------------------------
            # Cases where this employee is counselor or processor
            cases_progressed_q = db.execute(
                select(func.count()).select_from(Case).where(
                    and_(
                        or_(
                            Case.assigned_counselor_id == employee_id,
                            Case.assigned_processor_id == employee_id,
                            Case.assigned_visa_officer_id == employee_id,
                        ),
                        Case.updated_at >= period_start_dt,
                        Case.updated_at <= period_end_dt,
                    )
                )
            )
            cases_progressed = cases_progressed_q.scalar() or 0

            cases_closed_q = db.execute(
                select(func.count()).select_from(Case).where(
                    and_(
                        or_(
                            Case.assigned_counselor_id == employee_id,
                            Case.assigned_processor_id == employee_id,
                        ),
                        Case.closed_at >= period_start_dt,
                        Case.closed_at <= period_end_dt,
                        Case.is_active == False,  # noqa: E712
                    )
                )
            )
            cases_closed = cases_closed_q.scalar() or 0

            # -------------------------------------------------------------------
            # 4. Task metrics
            # -------------------------------------------------------------------
            tasks_completed_q = db.execute(
                select(func.count()).select_from(Task).where(
                    and_(
                        Task.assigned_to == employee_id,
                        Task.status == "completed",
                        Task.completed_at >= period_start_dt,
                        Task.completed_at <= period_end_dt,
                    )
                )
            )
            tasks_completed = tasks_completed_q.scalar() or 0

            tasks_overdue_q = db.execute(
                select(func.count()).select_from(Task).where(
                    and_(
                        Task.assigned_to == employee_id,
                        Task.status != "completed",
                        Task.due_at < period_end_dt,
                        Task.due_at >= period_start_dt,
                    )
                )
            )
            tasks_overdue = tasks_overdue_q.scalar() or 0

            # Average task completion time (hours)
            avg_task_hours_q = db.execute(
                select(
                    func.avg(
                        func.extract("epoch", Task.completed_at - Task.created_at) / 3600.0
                    )
                ).select_from(Task).where(
                    and_(
                        Task.assigned_to == employee_id,
                        Task.status == "completed",
                        Task.completed_at >= period_start_dt,
                        Task.completed_at <= period_end_dt,
                        Task.completed_at.isnot(None),
                    )
                )
            )
            avg_task_hours = avg_task_hours_q.scalar()
            avg_task_completion_hours = round(float(avg_task_hours), 2) if avg_task_hours else None

            # -------------------------------------------------------------------
            # 5. Document metrics
            # -------------------------------------------------------------------
            docs_processed_q = db.execute(
                select(func.count()).select_from(Document).where(
                    and_(
                        Document.uploaded_by == employee_id,
                        Document.created_at >= period_start_dt,
                        Document.created_at <= period_end_dt,
                    )
                )
            )
            documents_processed = docs_processed_q.scalar() or 0

            docs_verified_q = db.execute(
                select(func.count()).select_from(Document).where(
                    and_(
                        Document.verified_by == employee_id,
                        Document.is_verified == True,  # noqa: E712
                        Document.verified_at >= period_start_dt,
                        Document.verified_at <= period_end_dt,
                    )
                )
            )
            documents_verified = docs_verified_q.scalar() or 0

            # -------------------------------------------------------------------
            # 6. Attendance metrics
            # -------------------------------------------------------------------
            # Attendance uses text columns and employee_id FK to profiles.id
            # We need to match via legacy_supabase_id
            days_present = 0
            days_absent = 0
            days_late = 0
            total_hours_worked = 0.0
            checkin_times = []
            checkout_times = []

            profile_id = user.legacy_supabase_id
            if profile_id:
                # Attendance.date is Text like "2025-01-15"
                date_strings = []
                current_date = period_start
                while current_date <= period_end:
                    date_strings.append(current_date.isoformat())
                    current_date += timedelta(days=1)

                attendance_q = db.execute(
                    select(Attendance).where(
                        and_(
                            Attendance.employee_id == profile_id,
                            Attendance.date.in_(date_strings),
                        )
                    )
                )
                attendance_records = attendance_q.scalars().all()

                total_work_days = len(date_strings)
                # Exclude weekends (Saturday=5, Sunday=6)
                work_days_in_period = 0
                d = period_start
                while d <= period_end:
                    if d.weekday() < 5:  # Mon-Fri
                        work_days_in_period += 1
                    d += timedelta(days=1)

                for record in attendance_records:
                    has_checkin = record.checkinat and record.checkinat.strip()
                    has_checkout = record.checkoutat and record.checkoutat.strip()

                    if has_checkin:
                        days_present += 1
                        # Parse checkin time
                        try:
                            checkin_dt = _parse_time_string(record.checkinat)
                            if checkin_dt:
                                checkin_times.append(checkin_dt)
                                # Late if after 10:00 AM
                                if checkin_dt.hour >= 10 and checkin_dt.minute > 0:
                                    days_late += 1
                        except Exception:
                            pass

                        if has_checkout:
                            try:
                                checkout_dt = _parse_time_string(record.checkoutat)
                                if checkout_dt and checkin_dt:
                                    checkout_times.append(checkout_dt)
                                    hours = (
                                        checkout_dt.hour * 60 + checkout_dt.minute
                                        - checkin_dt.hour * 60 - checkin_dt.minute
                                    ) / 60.0
                                    if hours > 0:
                                        total_hours_worked += hours
                            except Exception:
                                pass

                days_absent = max(0, work_days_in_period - days_present)

            # Compute average check-in/check-out times
            avg_checkin = None
            avg_checkout = None
            if checkin_times:
                avg_minutes = sum(t.hour * 60 + t.minute for t in checkin_times) // len(checkin_times)
                avg_checkin = time(avg_minutes // 60, avg_minutes % 60)
            if checkout_times:
                avg_minutes = sum(t.hour * 60 + t.minute for t in checkout_times) // len(checkout_times)
                avg_checkout = time(avg_minutes // 60, avg_minutes % 60)

            total_hours_worked = round(total_hours_worked, 2)

            # -------------------------------------------------------------------
            # 7. Compute AI scores
            # -------------------------------------------------------------------
            # Simple weighted scoring (0-100 scale)
            raw_data = {
                "calls_made": calls_made,
                "calls_received": calls_received,
                "calls_missed": calls_missed,
                "cases_progressed": cases_progressed,
                "cases_closed": cases_closed,
                "tasks_completed": tasks_completed,
                "tasks_overdue": tasks_overdue,
                "days_present": days_present,
                "days_absent": days_absent,
                "total_hours_worked": total_hours_worked,
                "avg_call_quality": avg_call_quality,
                "documents_processed": documents_processed,
                "documents_verified": documents_verified,
            }

            # Performance score: weighted composite
            perf_components = []
            # Call activity (weight: 25%)
            total_calls = calls_made + calls_received
            if total_calls > 0:
                call_score = min(100, (total_calls / max(1, 10 if period_type == "daily" else 50 if period_type == "weekly" else 200)) * 100)
                perf_components.append(("calls", call_score, 0.25))
            # Case activity (weight: 25%)
            if cases_progressed > 0 or cases_closed > 0:
                case_score = min(100, ((cases_progressed + cases_closed * 2) / max(1, 5 if period_type == "daily" else 25 if period_type == "weekly" else 100)) * 100)
                perf_components.append(("cases", case_score, 0.25))
            # Task completion (weight: 25%)
            if tasks_completed > 0 or tasks_overdue > 0:
                task_total = tasks_completed + tasks_overdue
                task_score = (tasks_completed / task_total * 100) if task_total > 0 else 0
                perf_components.append(("tasks", task_score, 0.25))
            # Attendance (weight: 25%)
            if days_present > 0 or days_absent > 0:
                total_expected = days_present + days_absent
                attend_score = (days_present / total_expected * 100) if total_expected > 0 else 0
                perf_components.append(("attendance", attend_score, 0.25))

            if perf_components:
                total_weight = sum(w for _, _, w in perf_components)
                ai_performance_score = round(
                    sum(s * w for _, s, w in perf_components) / total_weight, 2
                )
            else:
                ai_performance_score = None

            # Efficiency score: based on avg task completion time and call duration
            efficiency_parts = []
            if avg_task_completion_hours is not None:
                # Lower is better: 24hrs = 50%, 4hrs = 100%, 48hrs+ = 20%
                eff = max(20, min(100, 100 - (avg_task_completion_hours - 4) * (80 / 44)))
                efficiency_parts.append(eff)
            if avg_call_duration_mins > 0:
                # Moderate duration (3-8 min) is best
                if 3 <= avg_call_duration_mins <= 8:
                    efficiency_parts.append(90)
                elif avg_call_duration_mins < 3:
                    efficiency_parts.append(60)  # Too short
                else:
                    efficiency_parts.append(max(40, 90 - (avg_call_duration_mins - 8) * 5))
            ai_efficiency_score = round(sum(efficiency_parts) / len(efficiency_parts), 2) if efficiency_parts else None

            # Quality score: based on call quality and document verification
            quality_parts = []
            if avg_call_quality is not None:
                quality_parts.append(avg_call_quality * 10)  # Convert 0-10 to 0-100
            if documents_verified > 0 and documents_processed > 0:
                quality_parts.append(min(100, (documents_verified / documents_processed) * 100))
            ai_quality_score = round(sum(quality_parts) / len(quality_parts), 2) if quality_parts else None

            # -------------------------------------------------------------------
            # 8. Upsert EmployeeMetric record
            # -------------------------------------------------------------------
            # Check if a metric for this employee/period already exists
            existing_q = db.execute(
                select(EmployeeMetric).where(
                    and_(
                        EmployeeMetric.employee_id == employee_id,
                        EmployeeMetric.period_type == period_type,
                        EmployeeMetric.period_start == period_start,
                        EmployeeMetric.period_end == period_end,
                    )
                )
            )
            metric = existing_q.scalar_one_or_none()

            if metric is None:
                metric = EmployeeMetric(
                    id=uuid.uuid4(),
                    employee_id=employee_id,
                    period_type=period_type,
                    period_start=period_start,
                    period_end=period_end,
                )
                db.add(metric)

            metric.calls_made = calls_made
            metric.calls_received = calls_received
            metric.calls_missed = calls_missed
            metric.total_call_duration_mins = total_call_duration_mins
            metric.avg_call_duration_mins = avg_call_duration_mins
            metric.avg_call_quality_score = avg_call_quality
            metric.avg_call_sentiment = avg_call_sentiment
            metric.leads_contacted = 0  # TODO: integrate with leads module
            metric.leads_converted = 0
            metric.new_students_onboarded = 0
            metric.cases_progressed = cases_progressed
            metric.cases_closed = cases_closed
            metric.applications_submitted = 0  # TODO: integrate with applications module
            metric.documents_processed = documents_processed
            metric.documents_verified = documents_verified
            metric.days_present = days_present
            metric.days_absent = days_absent
            metric.days_late = days_late
            metric.avg_checkin_time = avg_checkin
            metric.avg_checkout_time = avg_checkout
            metric.total_hours_worked = total_hours_worked
            metric.tasks_completed = tasks_completed
            metric.tasks_overdue = tasks_overdue
            metric.avg_task_completion_hours = avg_task_completion_hours
            metric.ai_performance_score = ai_performance_score
            metric.ai_efficiency_score = ai_efficiency_score
            metric.ai_quality_score = ai_quality_score
            metric.raw_data = raw_data
            metric.computed_at = datetime.now(timezone.utc)

            db.commit()

            logger.info(
                "Computed %s metrics for employee %s: perf=%.1f, eff=%s, qual=%s",
                period_type,
                employee_id,
                ai_performance_score or 0,
                ai_efficiency_score,
                ai_quality_score,
            )
            return {
                "employee_id": employee_id,
                "period_type": period_type,
                "status": "computed",
                "ai_performance_score": ai_performance_score,
            }

    except Exception as exc:
        logger.error("Failed to compute metrics for employee %s: %s", employee_id, exc)
        raise self.retry(exc=exc, countdown=120)


def _parse_time_string(time_str: str) -> time | None:
    """Parse a time string from attendance records. Handles various formats."""
    if not time_str or not time_str.strip():
        return None
    time_str = time_str.strip()
    # Try common formats
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.time()
        except ValueError:
            continue
    # Try to extract time from ISO format
    try:
        if "T" in time_str:
            time_part = time_str.split("T")[1].split("+")[0].split("Z")[0]
            dt = datetime.strptime(time_part, "%H:%M:%S")
            return dt.time()
    except (ValueError, IndexError):
        pass
    return None


# ---------------------------------------------------------------------------
# Task: process_document
# ---------------------------------------------------------------------------
@celery.task(name="process_document", bind=True, max_retries=3)
def process_document(self, document_id: str):
    """Process a document: download from S3, extract text, run AI extraction.

    Steps:
    1. Fetch Document record and validate file_key exists
    2. Download file from S3 to temp file
    3. Extract text (PDF extraction for PDFs, plain read for text)
    4. Run extract_document_data via OpenAI
    5. Update document record with ai_extracted_data
    """
    logger.info("Processing document %s", document_id)
    tmp_path = None
    try:
        from app.database import sync_session_factory
        from app.modules.documents.models import Document
        from app.core.openai_service import extract_document_data
        from sqlalchemy import select

        with sync_session_factory() as db:
            result = db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if not doc:
                logger.warning("Document %s not found", document_id)
                return {"document_id": document_id, "status": "not_found"}

            if not doc.file_key:
                logger.warning("Document %s has no file_key", document_id)
                return {"document_id": document_id, "status": "no_file"}

            # Determine extension from file name
            ext = ""
            if doc.file_name and "." in doc.file_name:
                ext = "." + doc.file_name.rsplit(".", 1)[-1]

            # Download from S3
            try:
                tmp_path = _download_s3_to_tempfile(doc.file_key, suffix=ext)
            except Exception as download_err:
                logger.error("Failed to download document %s from S3: %s", document_id, download_err)
                raise

            # Determine mime type
            mime_type = doc.mime_type
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(doc.file_name or "")
                mime_type = mime_type or "application/octet-stream"

            # Extract text
            try:
                text_content = _extract_text_from_file(tmp_path, mime_type)
            except Exception as extract_err:
                logger.error("Text extraction failed for document %s: %s", document_id, extract_err)
                doc.ai_extracted_data = {
                    "error": f"Text extraction failed: {str(extract_err)[:500]}",
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                }
                db.commit()
                raise

            if not text_content or len(text_content.strip()) < 5:
                doc.ai_extracted_data = {
                    "status": "no_text",
                    "message": "No meaningful text content could be extracted",
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                }
                db.commit()
                logger.info("Document %s processed but no text extracted", document_id)
                return {"document_id": document_id, "status": "no_text"}

            # Run AI extraction
            doc_type = doc.document_type or "general"
            max_chars = 30000
            truncated_text = text_content[:max_chars]

            try:
                extraction_result = asyncio.run(
                    extract_document_data(truncated_text, doc_type)
                )
            except Exception as ai_err:
                logger.error("AI extraction failed for document %s: %s", document_id, ai_err)
                doc.ai_extracted_data = {
                    "error": f"AI extraction failed: {str(ai_err)[:500]}",
                    "raw_text_preview": text_content[:1000],
                    "raw_text_length": len(text_content),
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                }
                db.commit()
                raise

            # Store results
            doc.ai_extracted_data = {
                "extraction": extraction_result,
                "raw_text_length": len(text_content),
                "ai_model_used": extraction_result.get("ai_model_used", "gpt-4o-mini"),
                "ai_tokens_used": extraction_result.get("ai_tokens_used", 0),
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
            db.commit()

            logger.info("Document %s processed successfully", document_id)
            return {"document_id": document_id, "status": "processed"}

    except Exception as exc:
        logger.error("Failed to process document %s: %s", document_id, exc)
        raise self.retry(exc=exc, countdown=60)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Task: cleanup_expired_tokens (EXISTING - kept as-is)
# ---------------------------------------------------------------------------
@celery.task(name="cleanup_expired_tokens")
def cleanup_expired_tokens():
    """Periodic task: clean up expired refresh tokens."""
    from app.database import sync_session_factory
    from app.modules.auth.models import RefreshToken
    from sqlalchemy import delete

    with sync_session_factory() as db:
        result = db.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            )
        )
        db.commit()
        count = result.rowcount
        logger.info("Cleaned up %d expired refresh tokens", count)
        return {"deleted": count}


# ---------------------------------------------------------------------------
# Batch tasks: called by Celery Beat to dispatch individual tasks
# ---------------------------------------------------------------------------
@celery.task(name="transcribe_call_batch")
def transcribe_call_batch():
    """Query CallAnalysis records with transcription_status='pending' and dispatch transcription tasks."""
    logger.info("Running transcribe_call_batch: looking for pending transcriptions")
    from app.database import sync_session_factory
    from app.modules.employee_automation.models import CallAnalysis
    from sqlalchemy import select, and_

    dispatched = 0
    try:
        with sync_session_factory() as db:
            result = db.execute(
                select(CallAnalysis.id).where(
                    and_(
                        CallAnalysis.transcription_status == "pending",
                        CallAnalysis.recording_url.isnot(None),
                        CallAnalysis.recording_url != "",
                    )
                ).limit(100)  # Process up to 100 per batch
            )
            pending_ids = [str(row[0]) for row in result.all()]

        for analysis_id in pending_ids:
            transcribe_call.delay(analysis_id)
            dispatched += 1

        logger.info("transcribe_call_batch dispatched %d tasks", dispatched)
        return {"dispatched": dispatched}
    except Exception as exc:
        logger.error("transcribe_call_batch failed: %s", exc)
        return {"dispatched": dispatched, "error": str(exc)}


@celery.task(name="compute_all_employee_metrics")
def compute_all_employee_metrics():
    """Query all active employees and dispatch compute_employee_metrics for each."""
    logger.info("Running compute_all_employee_metrics: dispatching daily metrics for all active employees")
    from app.database import sync_session_factory
    from app.modules.users.models import User
    from sqlalchemy import select

    dispatched = 0
    try:
        with sync_session_factory() as db:
            result = db.execute(
                select(User.id).where(User.is_active == True)  # noqa: E712
            )
            employee_ids = [str(row[0]) for row in result.all()]

        for emp_id in employee_ids:
            compute_employee_metrics.delay(emp_id, "daily")
            dispatched += 1

        logger.info("compute_all_employee_metrics dispatched %d tasks", dispatched)
        return {"dispatched": dispatched}
    except Exception as exc:
        logger.error("compute_all_employee_metrics failed: %s", exc)
        return {"dispatched": dispatched, "error": str(exc)}


@celery.task(name="process_file_ingestion_batch")
def process_file_ingestion_batch():
    """Query FileIngestion records with processing_status='pending' and dispatch processing tasks."""
    logger.info("Running process_file_ingestion_batch: looking for pending ingestions")
    from app.database import sync_session_factory
    from app.modules.employee_automation.models import FileIngestion
    from sqlalchemy import select

    dispatched = 0
    try:
        with sync_session_factory() as db:
            result = db.execute(
                select(FileIngestion.id).where(
                    FileIngestion.processing_status == "pending"
                ).limit(100)  # Process up to 100 per batch
            )
            pending_ids = [str(row[0]) for row in result.all()]

        for ingestion_id in pending_ids:
            process_file_ingestion.delay(ingestion_id)
            dispatched += 1

        logger.info("process_file_ingestion_batch dispatched %d tasks", dispatched)
        return {"dispatched": dispatched}
    except Exception as exc:
        logger.error("process_file_ingestion_batch failed: %s", exc)
        return {"dispatched": dispatched, "error": str(exc)}


# ---------------------------------------------------------------------------
# Task: detect_stuck_cases — mirrors Supabase Edge Function `eb-stuck-detector` (v2)
# ---------------------------------------------------------------------------
# Stage timeout thresholds (in days) matching the Edge Function
STAGE_TIMEOUTS = {
    "initial_consultation": 3,
    "documents_pending": 7,
    "documents_collected": 3,
    "university_shortlisted": 5,
    "applied": 14,
    "offer_received": 5,
    "offer_accepted": 7,
    "visa_processing": 30,
    "travel_booked": 14,
    "on_hold": 30,
}


@celery.task(name="detect_stuck_cases")
def detect_stuck_cases():
    """Detect cases stuck beyond stage timeouts and create follow-up tasks + notifications.

    Mirrors the Supabase Edge Function `eb-stuck-detector` (v2) which:
    1. Finds active cases where current_stage hasn't changed beyond the timeout threshold
    2. Creates follow-up tasks assigned to the case counselor
    3. Creates notifications for the counselor
    4. Escalates to admins if stuck > 2x the timeout threshold

    Runs daily via Celery Beat.
    """
    logger.info("Running stuck case detection")
    try:
        from app.database import sync_session_factory
        from app.modules.cases.models import Case
        from app.modules.tasks.models import Task as TaskModel
        from app.modules.notifications.models import Notification
        from app.modules.users.models import User, UserRole, Role
        from sqlalchemy import select, and_

        stuck_count = 0
        escalated_count = 0

        with sync_session_factory() as db:
            now = datetime.now(timezone.utc)

            # Find all active cases
            result = db.execute(
                select(Case).where(Case.is_active.is_(True))
            )
            active_cases = result.scalars().all()

            # Get admin user IDs for escalation
            admin_role_result = db.execute(
                select(Role.id).where(Role.name == "admin")
            )
            admin_role = admin_role_result.scalar_one_or_none()

            admin_ids = []
            if admin_role:
                admin_user_roles = db.execute(
                    select(UserRole.user_id).where(UserRole.role_id == admin_role)
                )
                admin_ids = [str(row[0]) for row in admin_user_roles.all()]

            for case in active_cases:
                stage = case.current_stage
                timeout_days = STAGE_TIMEOUTS.get(stage)
                if timeout_days is None:
                    continue  # No timeout for this stage (completed, cancelled, etc.)

                # Determine how long the case has been in this stage
                last_update = case.updated_at or case.created_at
                if last_update is None:
                    continue

                # Make timezone-aware if needed
                if last_update.tzinfo is None:
                    last_update = last_update.replace(tzinfo=timezone.utc)

                days_in_stage = (now - last_update).days

                if days_in_stage < timeout_days:
                    continue  # Not stuck yet

                stuck_count += 1
                counselor_id = case.assigned_counselor_id

                # Check if we already created a task for this stuck case recently (last 7 days)
                existing_task = db.execute(
                    select(TaskModel).where(
                        and_(
                            TaskModel.entity_type == "case",
                            TaskModel.entity_id == case.id,
                            TaskModel.task_type == "stuck_follow_up",
                            TaskModel.created_at >= now - timedelta(days=7),
                        )
                    )
                ).scalar_one_or_none()

                if existing_task:
                    continue  # Already flagged recently

                # Create follow-up task
                task = TaskModel(
                    id=uuid.uuid4(),
                    entity_type="case",
                    entity_id=case.id,
                    title=f"Stuck case: {stage} for {days_in_stage} days",
                    description=(
                        f"Case has been in '{stage}' stage for {days_in_stage} days "
                        f"(threshold: {timeout_days} days). Please review and take action."
                    ),
                    task_type="stuck_follow_up",
                    assigned_to=counselor_id,
                    priority="high" if days_in_stage >= timeout_days * 2 else "normal",
                    status="pending",
                    due_at=now + timedelta(days=1),
                    created_at=now,
                )
                db.add(task)

                # Notify the counselor
                if counselor_id:
                    notification = Notification(
                        id=uuid.uuid4(),
                        user_id=counselor_id,
                        title=f"Case stuck in {stage}",
                        message=(
                            f"A case has been in '{stage}' for {days_in_stage} days. "
                            f"Please review and progress it."
                        ),
                        notification_type="stuck_case",
                        entity_type="case",
                        entity_id=case.id,
                        created_at=now,
                    )
                    db.add(notification)

                    # Send FCM push for the counselor
                    send_fcm_push.delay(
                        str(counselor_id),
                        f"Case stuck in {stage}",
                        f"A case has been stuck for {days_in_stage} days. Please review.",
                        {"type": "stuck_case", "case_id": str(case.id)},
                    )

                # Escalate if stuck > 2x the timeout
                if days_in_stage >= timeout_days * 2:
                    escalated_count += 1
                    for admin_id in admin_ids:
                        admin_notification = Notification(
                            id=uuid.uuid4(),
                            user_id=admin_id,
                            title=f"ESCALATION: Case stuck {days_in_stage} days in {stage}",
                            message=(
                                f"Case {case.id} has been stuck in '{stage}' for {days_in_stage} days "
                                f"(2x threshold of {timeout_days} days). Immediate attention required."
                            ),
                            notification_type="escalation",
                            entity_type="case",
                            entity_id=case.id,
                            created_at=now,
                        )
                        db.add(admin_notification)

                        send_fcm_push.delay(
                            admin_id,
                            f"ESCALATION: Case stuck {days_in_stage}d",
                            f"Case stuck in '{stage}' for {days_in_stage} days. Needs immediate review.",
                            {"type": "escalation", "case_id": str(case.id)},
                        )

            db.commit()

        logger.info(
            "Stuck case detection complete: %d stuck, %d escalated",
            stuck_count, escalated_count,
        )
        return {"stuck": stuck_count, "escalated": escalated_count}

    except Exception as exc:
        logger.error("Stuck case detection failed: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task: parse_resume — mirrors Supabase Edge Function `parseresume` (v84)
# ---------------------------------------------------------------------------
@celery.task(name="parse_resume", bind=True, max_retries=3)
def parse_resume(self, file_ingestion_id: str):
    """Parse a resume PDF using OpenAI GPT-4o-mini with structured output.

    Mirrors the Supabase Edge Function `parseresume` which:
    1. Downloads the PDF file
    2. Uploads to OpenAI Files API
    3. Uses GPT-4o-mini Responses API with a JSON schema for structured extraction
    4. Returns structured resume data (personal_info, education, experience, skills, etc.)

    The result is stored in the FileIngestion.extracted_data field.
    """
    logger.info("Parsing resume for file ingestion %s", file_ingestion_id)
    tmp_path = None
    try:
        from app.database import sync_session_factory
        from app.modules.employee_automation.models import FileIngestion
        from sqlalchemy import select

        with sync_session_factory() as db:
            result = db.execute(select(FileIngestion).where(FileIngestion.id == file_ingestion_id))
            ingestion = result.scalar_one_or_none()
            if not ingestion:
                logger.warning("File ingestion %s not found", file_ingestion_id)
                return {"file_ingestion_id": file_ingestion_id, "status": "not_found"}

            # Mark as processing
            ingestion.processing_status = "processing"
            db.commit()

            # Download file from S3
            file_key = ingestion.file_key
            file_name = ingestion.file_name or "resume.pdf"
            ext = "." + file_name.rsplit(".", 1)[-1] if "." in file_name else ".pdf"

            if not file_key:
                ingestion.processing_status = "failed"
                ingestion.processing_error = "No file_key"
                db.commit()
                return {"file_ingestion_id": file_ingestion_id, "status": "no_file"}

            try:
                tmp_path = _download_s3_to_tempfile(file_key, suffix=ext)
            except Exception as dl_err:
                logger.error("Download failed for %s: %s", file_ingestion_id, dl_err)
                ingestion.processing_status = "failed"
                ingestion.processing_error = f"Download failed: {str(dl_err)[:500]}"
                db.commit()
                raise

            # Extract text from PDF
            try:
                text_content = _extract_text_from_pdf(tmp_path)
            except Exception as extract_err:
                logger.error("PDF text extraction failed for %s: %s", file_ingestion_id, extract_err)
                ingestion.processing_status = "failed"
                ingestion.processing_error = f"PDF extraction failed: {str(extract_err)[:500]}"
                db.commit()
                raise

            if not text_content or len(text_content.strip()) < 20:
                ingestion.processing_status = "failed"
                ingestion.processing_error = "No meaningful text extracted from PDF"
                db.commit()
                return {"file_ingestion_id": file_ingestion_id, "status": "no_text"}

            # Run structured extraction via OpenAI
            try:
                from app.core.openai_service import get_openai_client
                import json

                client_sync = asyncio.run(_get_resume_extraction(text_content))
                resume_data = client_sync
            except Exception as ai_err:
                logger.error("AI resume extraction failed for %s: %s", file_ingestion_id, ai_err)
                # Still save raw text
                ingestion.extracted_data = {
                    "type": "resume",
                    "raw_text": text_content[:5000],
                    "ai_error": str(ai_err)[:500],
                }
                ingestion.processing_status = "completed"
                ingestion.processing_completed_at = datetime.now(timezone.utc)
                db.commit()
                return {"file_ingestion_id": file_ingestion_id, "status": "partial", "detail": "ai_failed"}

            # Store structured resume data
            ingestion.extracted_data = {
                "type": "resume",
                "parsed_data": resume_data,
                "raw_text_length": len(text_content),
            }
            ingestion.ai_model_used = resume_data.get("ai_model_used", "gpt-4o-mini")
            ingestion.ai_tokens_used = resume_data.get("ai_tokens_used", 0)
            ingestion.processing_status = "completed"
            ingestion.processing_completed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info("Resume parsed successfully for %s", file_ingestion_id)
            return {"file_ingestion_id": file_ingestion_id, "status": "completed"}

    except Exception as exc:
        logger.error("Resume parsing failed for %s: %s", file_ingestion_id, exc)
        try:
            from app.database import sync_session_factory as sf
            from app.modules.employee_automation.models import FileIngestion as FI
            from sqlalchemy import update as upd

            with sf() as db2:
                db2.execute(
                    upd(FI).where(FI.id == file_ingestion_id)
                    .values(processing_status="failed", processing_error=str(exc)[:2000])
                )
                db2.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


async def _get_resume_extraction(text_content: str) -> dict:
    """Extract structured resume data using OpenAI GPT-4o-mini.

    Mirrors the parseresume Edge Function's JSON schema extraction.
    """
    from app.core.openai_service import get_openai_client
    import json

    client = get_openai_client()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert resume parser. Extract structured data from the resume text. "
                    "Return a JSON object with these fields:\n"
                    "- personal_info: {full_name, email, phone, address, linkedin, date_of_birth, nationality}\n"
                    "- education: [{institution, degree, field_of_study, start_date, end_date, grade_or_gpa}]\n"
                    "- work_experience: [{company, title, start_date, end_date, description, responsibilities}]\n"
                    "- skills: {technical: [], soft: [], languages: [], certifications: []}\n"
                    "- english_proficiency: {test_type, overall_score, listening, reading, writing, speaking}\n"
                    "- summary: brief 2-3 sentence professional summary\n"
                    "- preferred_countries: [] (if mentioned)\n"
                    "- preferred_programs: [] (if mentioned)\n"
                    "Use null for missing fields. Return ONLY valid JSON."
                ),
            },
            {"role": "user", "content": text_content[:25000]},  # Truncate to ~6K tokens
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    content = response.choices[0].message.content
    tokens_used = response.usage.total_tokens if response.usage else 0
    result = json.loads(content)
    result["ai_tokens_used"] = tokens_used
    result["ai_model_used"] = "gpt-4o-mini"
    return result
