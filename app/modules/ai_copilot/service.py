"""AI Copilot service — next-action suggestions, lead scoring, case steps, and email drafts."""

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.openai_service import chat_completion
from app.modules.approvals.service import create_ai_draft

logger = logging.getLogger("empireo.ai_copilot")


# ---------------------------------------------------------------------------
# 1. Suggest next action for a student
# ---------------------------------------------------------------------------

async def suggest_next_action(db: AsyncSession, student_id: UUID) -> dict:
    """Analyze a student's situation and suggest the best next action."""
    from app.modules.students.models import Student
    from app.modules.cases.models import Case
    from app.modules.call_events.models import CallEvent
    from app.modules.tasks.models import Task

    # Load student
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError(f"Student {student_id} not found")

    # Load case(s) for this student
    result = await db.execute(
        select(Case).where(Case.student_id == student_id).order_by(Case.created_at.desc())
    )
    cases = result.scalars().all()

    # Load recent tasks
    result = await db.execute(
        select(Task)
        .where(Task.entity_type == "student", Task.entity_id == student_id)
        .order_by(Task.created_at.desc())
        .limit(5)
    )
    tasks = result.scalars().all()

    # Load recent call events for this student's phone (if available)
    recent_calls = []
    if student.phone:
        result = await db.execute(
            select(CallEvent)
            .where(CallEvent.caller_phone_norm == student.phone)
            .order_by(CallEvent.created_at.desc())
            .limit(5)
        )
        recent_calls = result.scalars().all()

    # Build context for AI
    case_info = []
    for c in cases:
        case_info.append({
            "case_id": str(c.id),
            "case_type": c.case_type,
            "current_stage": c.current_stage,
            "priority": c.priority,
            "is_active": c.is_active,
        })

    task_info = []
    for t in tasks:
        task_info.append({
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "due_at": str(t.due_at) if t.due_at else None,
        })

    call_info = []
    for ce in recent_calls:
        call_info.append({
            "event_type": ce.event_type,
            "call_status": ce.call_status,
            "duration": ce.conversation_duration,
            "date": str(ce.created_at) if ce.created_at else None,
        })

    student_context = {
        "student_id": str(student.id),
        "full_name": student.full_name,
        "email": student.email,
        "phone": student.phone,
        "education_level": student.education_level,
        "english_test_type": student.english_test_type,
        "english_test_score": student.english_test_score,
        "preferred_countries": student.preferred_countries,
        "preferred_programs": student.preferred_programs,
    }

    prompt = (
        "You are an expert counselor assistant for a study abroad consultancy called Empireo. "
        "Analyze the student's profile, their case status, recent tasks, and call history. "
        "Suggest the single best next action for a counselor to take.\n\n"
        "Return a JSON object with these fields:\n"
        "- suggested_action: string describing the action in plain English\n"
        "- action_type: one of [stage_transition, send_notification, follow_up, assign_counselor, update_student, docs_request]\n"
        "- reason: why this action is recommended\n"
        "- urgency: one of [high, medium, low]\n"
        "- draft_message: optional message text if applicable\n"
        "- confidence: float 0.0-1.0\n"
        "- payload: a dict with action-specific data (e.g. {new_stage: ...} for stage_transition)\n\n"
        "Return ONLY valid JSON."
    )

    context = (
        f"Student: {json.dumps(student_context)}\n\n"
        f"Cases: {json.dumps(case_info)}\n\n"
        f"Recent Tasks: {json.dumps(task_info)}\n\n"
        f"Recent Calls: {json.dumps(call_info)}"
    )

    ai_response = await chat_completion(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": context},
        ],
        json_mode=True,
        temperature=0.3,
    )

    suggestion = json.loads(ai_response["content"])

    # Ensure all expected fields are present with defaults
    suggestion.setdefault("suggested_action", "No suggestion available")
    suggestion.setdefault("action_type", "follow_up")
    suggestion.setdefault("reason", "")
    suggestion.setdefault("urgency", "medium")
    suggestion.setdefault("draft_message", None)
    suggestion.setdefault("confidence", 0.5)
    suggestion.setdefault("payload", {})

    # Auto-create an ActionDraft if confidence is high enough
    if suggestion["confidence"] > 0.7 and cases:
        primary_case = cases[0]
        try:
            await create_ai_draft(
                db=db,
                action_type=suggestion["action_type"],
                entity_type="case" if suggestion["action_type"] in ("stage_transition", "assign_counselor") else "student",
                entity_id=primary_case.id if suggestion["action_type"] in ("stage_transition", "assign_counselor") else student_id,
                payload=suggestion["payload"],
                reason=suggestion["reason"],
            )
        except Exception:
            logger.warning("Failed to auto-create ActionDraft for student %s", student_id, exc_info=True)

    return suggestion


# ---------------------------------------------------------------------------
# 2. Score a lead (rule-based)
# ---------------------------------------------------------------------------

async def score_lead(db: AsyncSession, lead_id: int) -> dict:
    """Score a lead based on profile completeness and engagement signals."""
    from app.modules.leads.models import Lead, LeadInfo
    from app.modules.call_events.models import CallEvent

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError(f"Lead {lead_id} not found")

    result = await db.execute(select(LeadInfo).where(LeadInfo.id == lead_id))
    lead_info = result.scalar_one_or_none()

    score = 0
    factors = []

    # Basic contact info (up to 20 pts)
    if lead.email:
        score += 10
        factors.append("Has email address")
    if lead.phone:
        score += 10
        factors.append("Has phone number")

    # Assigned counselor (10 pts)
    if lead.assigned_to:
        score += 10
        factors.append("Has assigned counselor")

    # Country preference (5 pts)
    if lead.country_preference and len(lead.country_preference) > 0:
        score += 5
        factors.append(f"Country preferences set ({len(lead.country_preference)})")

    # Lead info completeness (up to 35 pts)
    if lead_info:
        if lead_info.education and lead_info.education != {}:
            score += 10
            factors.append("Education info provided")
        if lead_info.basic_info and lead_info.basic_info != {}:
            score += 5
            factors.append("Basic info provided")
        if lead_info.budget_info and lead_info.budget_info != {}:
            score += 10
            factors.append("Budget info provided")
        if lead_info.preferences and lead_info.preferences != {}:
            score += 5
            factors.append("Preferences set")
        if lead_info.english_proficiency and lead_info.english_proficiency != {}:
            score += 5
            factors.append("English proficiency info provided")

    # Recent call activity (up to 15 pts)
    if lead.phone:
        phone_str = str(lead.phone)
        result = await db.execute(
            select(CallEvent)
            .where(CallEvent.caller_phone_norm == phone_str)
            .order_by(CallEvent.created_at.desc())
            .limit(5)
        )
        recent_calls = result.scalars().all()
        if recent_calls:
            call_count = len(recent_calls)
            score += min(call_count * 5, 15)
            factors.append(f"Recent call activity ({call_count} calls)")

    # Registration status (5 pts)
    if lead.is_registered:
        score += 5
        factors.append("Registered user")

    # Cap at 100
    score = min(score, 100)

    # Determine heat status
    if score >= 70:
        heat_status = "hot"
    elif score >= 40:
        heat_status = "warm"
    else:
        heat_status = "cold"

    # Recommend action
    if heat_status == "hot":
        recommended_action = "Schedule immediate consultation — high-value lead"
    elif heat_status == "warm":
        recommended_action = "Send follow-up with relevant course suggestions"
    else:
        recommended_action = "Send introductory materials and check back later"

    return {
        "lead_id": lead_id,
        "score": score,
        "heat_status": heat_status,
        "factors": factors,
        "recommended_action": recommended_action,
    }


# ---------------------------------------------------------------------------
# 3. Suggest case next step
# ---------------------------------------------------------------------------

async def suggest_case_next_step(db: AsyncSession, case_id: UUID) -> dict:
    """Analyze a case and suggest the next stage transition."""
    from app.modules.cases.models import Case, VALID_STAGES
    from app.modules.applications.models import Application
    from app.modules.documents.models import Document

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError(f"Case {case_id} not found")

    # Load student via the relationship (already selectin loaded)
    student = case.student

    # Load applications for this case
    result = await db.execute(
        select(Application).where(Application.case_id == case_id)
    )
    applications = result.scalars().all()

    # Load documents for the student
    documents = []
    if student:
        result = await db.execute(
            select(Document).where(
                Document.entity_type == "student",
                Document.entity_id == student.id,
            )
        )
        documents = result.scalars().all()

    app_info = []
    for a in applications:
        app_info.append({
            "university": a.university_name,
            "program": a.program_name,
            "status": a.status,
            "offer_details": a.offer_details,
        })

    doc_info = []
    for d in documents:
        doc_info.append({
            "document_type": d.document_type,
            "is_verified": d.is_verified,
            "file_name": d.file_name,
        })

    case_context = {
        "case_id": str(case.id),
        "case_type": case.case_type,
        "current_stage": case.current_stage,
        "priority": case.priority,
        "is_active": case.is_active,
        "target_intake": case.target_intake,
        "notes": case.notes,
        "student_name": student.full_name if student else None,
    }

    prompt = (
        "You are a case management expert for Empireo, a study abroad consultancy. "
        "Analyze the case, its applications, and documents to suggest the next step.\n\n"
        f"Valid stages in order: {', '.join(VALID_STAGES)}\n\n"
        "Return a JSON object with these fields:\n"
        "- case_id: the case UUID as string\n"
        "- current_stage: the current stage\n"
        "- suggested_next_stage: the recommended next stage\n"
        "- reason: why this transition makes sense\n"
        "- blockers: list of strings describing what might block this transition\n"
        "- estimated_days: integer estimate of days until transition, or null\n\n"
        "Return ONLY valid JSON."
    )

    context = (
        f"Case: {json.dumps(case_context)}\n\n"
        f"Applications: {json.dumps(app_info)}\n\n"
        f"Documents: {json.dumps(doc_info)}"
    )

    ai_response = await chat_completion(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": context},
        ],
        json_mode=True,
        temperature=0.3,
    )

    result_data = json.loads(ai_response["content"])

    # Ensure required fields with defaults
    result_data.setdefault("case_id", str(case_id))
    result_data.setdefault("current_stage", case.current_stage)
    result_data.setdefault("suggested_next_stage", case.current_stage)
    result_data.setdefault("reason", "")
    result_data.setdefault("blockers", [])
    result_data.setdefault("estimated_days", None)

    return result_data


# ---------------------------------------------------------------------------
# 4. Draft an email
# ---------------------------------------------------------------------------

async def draft_email(db: AsyncSession, entity_type: str, entity_id: str, email_type: str) -> dict:
    """Generate an email draft for a student or lead."""

    entity_context = {}

    if entity_type == "student":
        from app.modules.students.models import Student

        result = await db.execute(select(Student).where(Student.id == entity_id))
        student = result.scalar_one_or_none()
        if not student:
            raise NotFoundError(f"Student {entity_id} not found")
        entity_context = {
            "name": student.full_name,
            "email": student.email,
            "education_level": student.education_level,
            "preferred_countries": student.preferred_countries,
            "preferred_programs": student.preferred_programs,
        }

    elif entity_type == "lead":
        from app.modules.leads.models import Lead, LeadInfo

        result = await db.execute(select(Lead).where(Lead.id == int(entity_id)))
        lead = result.scalar_one_or_none()
        if not lead:
            raise NotFoundError(f"Lead {entity_id} not found")

        result = await db.execute(select(LeadInfo).where(LeadInfo.id == int(entity_id)))
        lead_info = result.scalar_one_or_none()

        entity_context = {
            "name": lead.name,
            "email": lead.email,
            "country_preference": lead.country_preference,
            "status": lead.status,
            "education": lead_info.education if lead_info else None,
        }
    else:
        raise NotFoundError(f"Unsupported entity_type: {entity_type}")

    # Map email_type to tone and purpose
    type_config = {
        "follow_up": {
            "purpose": "Follow up with the student/lead after initial consultation",
            "tone": "friendly and professional",
            "attachments": ["course brochure", "consultation notes"],
        },
        "offer_congrats": {
            "purpose": "Congratulate the student on receiving an offer from a university",
            "tone": "warm and celebratory",
            "attachments": ["offer acceptance guide", "next steps checklist"],
        },
        "docs_request": {
            "purpose": "Request missing or additional documents from the student/lead",
            "tone": "professional and clear",
            "attachments": ["document checklist", "upload instructions"],
        },
        "payment_reminder": {
            "purpose": "Remind about an upcoming or overdue payment",
            "tone": "polite but firm",
            "attachments": ["payment invoice", "payment methods guide"],
        },
    }

    config = type_config.get(email_type, {
        "purpose": f"General email regarding {email_type}",
        "tone": "professional",
        "attachments": [],
    })

    prompt = (
        "You are a professional email writer for Empireo, a study abroad consultancy. "
        f"Write a {config['tone']} email for the following purpose: {config['purpose']}.\n\n"
        "The email should be personalized based on the recipient's information.\n\n"
        "Return a JSON object with these fields:\n"
        "- subject: the email subject line\n"
        "- body: the full email body (use \\n for line breaks)\n"
        "- tone: the tone used\n"
        "- suggested_attachments: list of suggested attachments to include\n\n"
        "Return ONLY valid JSON."
    )

    context = f"Recipient info: {json.dumps(entity_context)}"

    ai_response = await chat_completion(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": context},
        ],
        json_mode=True,
        temperature=0.5,
    )

    result_data = json.loads(ai_response["content"])

    # Ensure required fields with defaults
    result_data.setdefault("subject", f"{email_type.replace('_', ' ').title()} — Empireo")
    result_data.setdefault("body", "")
    result_data.setdefault("tone", config["tone"])
    result_data.setdefault("suggested_attachments", config["attachments"])

    return result_data
