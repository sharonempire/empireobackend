"""Employee automation endpoints — file ingestion, call analysis, metrics, reviews, goals, schedules, training."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.employee_automation import service
from app.modules.employee_automation.schemas import (
    CallAnalysisCreate,
    CallAnalysisOut,
    EmployeeGoalCreate,
    EmployeeGoalOut,
    EmployeeGoalUpdate,
    EmployeeMetricOut,
    EmployeePatternOut,
    EmployeeScheduleCreate,
    EmployeeScheduleOut,
    EmployeeScheduleUpdate,
    FileIngestionCreate,
    FileIngestionOut,
    PerformanceReviewCreate,
    PerformanceReviewOut,
    PerformanceReviewUpdate,
    TrainingRecordCreate,
    TrainingRecordOut,
    TrainingRecordUpdate,
    WorkLogCreate,
    WorkLogOut,
)
from app.modules.users.models import User

router = APIRouter(prefix="/employee-automation", tags=["Employee Automation"])


# ==================== File Ingestion ====================

@router.get("/file-ingestions", response_model=PaginatedResponse[FileIngestionOut])
async def api_list_file_ingestions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    employee_id: UUID | None = None,
    processing_status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_file_ingestions(db, page, size, employee_id, processing_status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/file-ingestions/{ingestion_id}", response_model=FileIngestionOut)
async def api_get_file_ingestion(
    ingestion_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_file_ingestion(db, ingestion_id)


@router.post("/file-ingestions", response_model=FileIngestionOut, status_code=201)
async def api_create_file_ingestion(
    data: FileIngestionCreate,
    current_user: User = Depends(require_perm("employee_automation", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_file_ingestion(db, data, uploaded_by=current_user.id)
    await log_event(db, "file_ingestion.created", current_user.id, "file_ingestion", item.id,
                    {"file_name": item.file_name})
    await db.commit()
    return item


# ==================== Call Analysis ====================

@router.get("/call-analyses", response_model=PaginatedResponse[CallAnalysisOut])
async def api_list_call_analyses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    employee_id: UUID | None = None,
    transcription_status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_call_analyses(db, page, size, employee_id, transcription_status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/call-analyses/{analysis_id}", response_model=CallAnalysisOut)
async def api_get_call_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_call_analysis(db, analysis_id)


@router.post("/call-analyses", response_model=CallAnalysisOut, status_code=201)
async def api_create_call_analysis(
    data: CallAnalysisCreate,
    current_user: User = Depends(require_perm("employee_automation", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_call_analysis(db, data)
    await log_event(db, "call_analysis.created", current_user.id, "call_analysis", item.id,
                    {"call_uuid": item.call_uuid})
    await db.commit()
    return item


# ==================== Employee Metrics ====================

@router.get("/metrics", response_model=PaginatedResponse[EmployeeMetricOut])
async def api_list_employee_metrics(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    employee_id: UUID | None = None,
    period_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_employee_metrics(db, page, size, employee_id, period_type)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/metrics/{metric_id}", response_model=EmployeeMetricOut)
async def api_get_employee_metric(
    metric_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_employee_metric(db, metric_id)


# ==================== Performance Reviews ====================

@router.get("/reviews", response_model=PaginatedResponse[PerformanceReviewOut])
async def api_list_performance_reviews(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    employee_id: UUID | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_performance_reviews(db, page, size, employee_id, status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/reviews/{review_id}", response_model=PerformanceReviewOut)
async def api_get_performance_review(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_performance_review(db, review_id)


@router.post("/reviews", response_model=PerformanceReviewOut, status_code=201)
async def api_create_performance_review(
    data: PerformanceReviewCreate,
    current_user: User = Depends(require_perm("employee_automation", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_performance_review(db, data, reviewer_id=current_user.id)
    await log_event(db, "performance_review.created", current_user.id, "performance_review", item.id,
                    {"employee_id": str(item.employee_id), "review_type": item.review_type})
    await db.commit()
    return item


@router.patch("/reviews/{review_id}", response_model=PerformanceReviewOut)
async def api_update_performance_review(
    review_id: UUID,
    data: PerformanceReviewUpdate,
    current_user: User = Depends(require_perm("employee_automation", "update")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.update_performance_review(db, review_id, data)
    await log_event(db, "performance_review.updated", current_user.id, "performance_review", item.id,
                    data.model_dump(exclude_unset=True))
    await db.commit()
    return item


# ==================== Employee Goals ====================

@router.get("/goals", response_model=PaginatedResponse[EmployeeGoalOut])
async def api_list_employee_goals(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    employee_id: UUID | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_employee_goals(db, page, size, employee_id, status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/goals/{goal_id}", response_model=EmployeeGoalOut)
async def api_get_employee_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_employee_goal(db, goal_id)


@router.post("/goals", response_model=EmployeeGoalOut, status_code=201)
async def api_create_employee_goal(
    data: EmployeeGoalCreate,
    current_user: User = Depends(require_perm("employee_automation", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_employee_goal(db, data, created_by=current_user.id)
    await log_event(db, "employee_goal.created", current_user.id, "employee_goal", item.id,
                    {"title": item.title, "employee_id": str(item.employee_id)})
    await db.commit()
    return item


@router.patch("/goals/{goal_id}", response_model=EmployeeGoalOut)
async def api_update_employee_goal(
    goal_id: UUID,
    data: EmployeeGoalUpdate,
    current_user: User = Depends(require_perm("employee_automation", "update")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.update_employee_goal(db, goal_id, data)
    await log_event(db, "employee_goal.updated", current_user.id, "employee_goal", item.id,
                    data.model_dump(exclude_unset=True))
    await db.commit()
    return item


# ==================== Work Logs ====================

@router.get("/work-logs", response_model=PaginatedResponse[WorkLogOut])
async def api_list_work_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    employee_id: UUID | None = None,
    activity_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_work_logs(db, page, size, employee_id, activity_type)
    return {**paginate_metadata(total, page, size), "items": items}


@router.post("/work-logs", response_model=WorkLogOut, status_code=201)
async def api_create_work_log(
    data: WorkLogCreate,
    current_user: User = Depends(require_perm("employee_automation", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_work_log(db, data)
    await log_event(db, "work_log.created", current_user.id, "work_log", item.id,
                    {"activity_type": item.activity_type, "employee_id": str(item.employee_id)})
    await db.commit()
    return item


# ==================== Employee Patterns ====================

@router.get("/patterns", response_model=PaginatedResponse[EmployeePatternOut])
async def api_list_employee_patterns(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    employee_id: UUID | None = None,
    is_active: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_employee_patterns(db, page, size, employee_id, is_active)
    return {**paginate_metadata(total, page, size), "items": items}


# ==================== Schedules ====================

@router.get("/schedules", response_model=PaginatedResponse[EmployeeScheduleOut])
async def api_list_employee_schedules(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    employee_id: UUID | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_employee_schedules(db, page, size, employee_id, status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/schedules/{schedule_id}", response_model=EmployeeScheduleOut)
async def api_get_employee_schedule(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_employee_schedule(db, schedule_id)


@router.post("/schedules", response_model=EmployeeScheduleOut, status_code=201)
async def api_create_employee_schedule(
    data: EmployeeScheduleCreate,
    current_user: User = Depends(require_perm("employee_automation", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_employee_schedule(db, data, approved_by=current_user.id)
    await log_event(db, "employee_schedule.created", current_user.id, "employee_schedule", item.id,
                    {"employee_id": str(item.employee_id), "schedule_type": item.schedule_type})
    await db.commit()
    return item


@router.patch("/schedules/{schedule_id}", response_model=EmployeeScheduleOut)
async def api_update_employee_schedule(
    schedule_id: UUID,
    data: EmployeeScheduleUpdate,
    current_user: User = Depends(require_perm("employee_automation", "update")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.update_employee_schedule(db, schedule_id, data)
    await log_event(db, "employee_schedule.updated", current_user.id, "employee_schedule", item.id,
                    data.model_dump(exclude_unset=True))
    await db.commit()
    return item


# ==================== Training Records ====================

@router.get("/training", response_model=PaginatedResponse[TrainingRecordOut])
async def api_list_training_records(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    employee_id: UUID | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_training_records(db, page, size, employee_id, status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/training/{record_id}", response_model=TrainingRecordOut)
async def api_get_training_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_training_record(db, record_id)


@router.post("/training", response_model=TrainingRecordOut, status_code=201)
async def api_create_training_record(
    data: TrainingRecordCreate,
    current_user: User = Depends(require_perm("employee_automation", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_training_record(db, data, assigned_by=current_user.id)
    await log_event(db, "training_record.created", current_user.id, "training_record", item.id,
                    {"title": item.title, "employee_id": str(item.employee_id)})
    await db.commit()
    return item


@router.patch("/training/{record_id}", response_model=TrainingRecordOut)
async def api_update_training_record(
    record_id: UUID,
    data: TrainingRecordUpdate,
    current_user: User = Depends(require_perm("employee_automation", "update")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.update_training_record(db, record_id, data)
    await log_event(db, "training_record.updated", current_user.id, "training_record", item.id,
                    data.model_dump(exclude_unset=True))
    await db.commit()
    return item


# ==================== Resume Parsing ====================
# Mirrors Supabase Edge Function `parseresume` (v84)


@router.post("/file-ingestions/{ingestion_id}/parse-resume", status_code=202)
async def api_parse_resume(
    ingestion_id: UUID,
    current_user: User = Depends(require_perm("employee_automation", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Trigger resume parsing for a file ingestion.

    Dispatches an async Celery task that:
    1. Downloads the PDF from S3
    2. Extracts text from PDF
    3. Uses GPT-4o-mini to extract structured resume data
    4. Stores result in extracted_data JSONB field

    Mirrors the Supabase Edge Function `parseresume` (v84).
    """
    # Verify the ingestion exists
    ingestion = await service.get_file_ingestion(db, ingestion_id)
    await log_event(db, "resume.parse_requested", current_user.id, "file_ingestion", str(ingestion_id), {
        "file_name": ingestion.file_name,
    })
    await db.commit()

    # Dispatch Celery task
    from app.workers.tasks import parse_resume
    parse_resume.delay(str(ingestion_id))

    return {
        "file_ingestion_id": str(ingestion_id),
        "status": "queued",
        "message": "Resume parsing task has been queued. Check file ingestion status for results.",
    }


# ==================== Stuck Case Detection (manual trigger) ====================


@router.post("/detect-stuck-cases", status_code=202)
async def api_detect_stuck_cases(
    current_user: User = Depends(require_perm("employee_automation", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger stuck case detection.

    Normally runs daily via Celery Beat, but can be triggered manually.
    Mirrors the Supabase Edge Function `eb-stuck-detector` (v2).
    """
    await log_event(db, "stuck_detection.manual_trigger", current_user.id, "system", "stuck_detector", {})
    await db.commit()

    from app.workers.tasks import detect_stuck_cases
    detect_stuck_cases.delay()

    return {
        "status": "queued",
        "message": "Stuck case detection task has been queued.",
    }


# ==================== Compute Metrics (manual trigger) ====================


@router.post("/compute-metrics/{employee_id}", status_code=202)
async def api_compute_metrics(
    employee_id: UUID,
    period_type: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    current_user: User = Depends(require_perm("employee_automation", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger employee metrics computation.

    Normally runs daily via Celery Beat, but can be triggered per-employee.
    """
    await log_event(db, "metrics.manual_compute", current_user.id, "employee_metric", str(employee_id), {
        "period_type": period_type,
    })
    await db.commit()

    from app.workers.tasks import compute_employee_metrics
    compute_employee_metrics.delay(str(employee_id), period_type)

    return {
        "employee_id": str(employee_id),
        "period_type": period_type,
        "status": "queued",
    }
