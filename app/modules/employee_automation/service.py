"""Employee automation service layer."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.employee_automation.models import (
    CallAnalysis,
    EmployeeGoal,
    EmployeeMetric,
    EmployeePattern,
    EmployeeSchedule,
    FileIngestion,
    PerformanceReview,
    TrainingRecord,
    WorkLog,
)
from app.modules.employee_automation.schemas import (
    CallAnalysisCreate,
    EmployeeGoalCreate,
    EmployeeGoalUpdate,
    EmployeeScheduleCreate,
    EmployeeScheduleUpdate,
    FileIngestionCreate,
    PerformanceReviewCreate,
    PerformanceReviewUpdate,
    TrainingRecordCreate,
    TrainingRecordUpdate,
    WorkLogCreate,
)


# --------------- File Ingestion ---------------

async def list_file_ingestions(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    employee_id: UUID | None = None,
    processing_status: str | None = None,
) -> tuple[list[FileIngestion], int]:
    stmt = select(FileIngestion)
    count_stmt = select(func.count()).select_from(FileIngestion)

    if employee_id:
        stmt = stmt.where(FileIngestion.employee_id == employee_id)
        count_stmt = count_stmt.where(FileIngestion.employee_id == employee_id)
    if processing_status:
        stmt = stmt.where(FileIngestion.processing_status == processing_status)
        count_stmt = count_stmt.where(FileIngestion.processing_status == processing_status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(FileIngestion.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_file_ingestion(db: AsyncSession, ingestion_id: UUID) -> FileIngestion:
    result = await db.execute(select(FileIngestion).where(FileIngestion.id == ingestion_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("File ingestion not found")
    return item


async def create_file_ingestion(db: AsyncSession, data: FileIngestionCreate, uploaded_by: UUID) -> FileIngestion:
    item = FileIngestion(**data.model_dump(), uploaded_by=uploaded_by, processing_status="pending")
    item.created_at = datetime.now(timezone.utc)
    db.add(item)
    await db.flush()
    return item


# --------------- Call Analysis ---------------

async def list_call_analyses(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    employee_id: UUID | None = None,
    transcription_status: str | None = None,
) -> tuple[list[CallAnalysis], int]:
    stmt = select(CallAnalysis)
    count_stmt = select(func.count()).select_from(CallAnalysis)

    if employee_id:
        stmt = stmt.where(CallAnalysis.employee_id == employee_id)
        count_stmt = count_stmt.where(CallAnalysis.employee_id == employee_id)
    if transcription_status:
        stmt = stmt.where(CallAnalysis.transcription_status == transcription_status)
        count_stmt = count_stmt.where(CallAnalysis.transcription_status == transcription_status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(CallAnalysis.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_call_analysis(db: AsyncSession, analysis_id: UUID) -> CallAnalysis:
    result = await db.execute(select(CallAnalysis).where(CallAnalysis.id == analysis_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Call analysis not found")
    return item


async def create_call_analysis(db: AsyncSession, data: CallAnalysisCreate) -> CallAnalysis:
    item = CallAnalysis(**data.model_dump(), transcription_status="pending")
    item.created_at = datetime.now(timezone.utc)
    db.add(item)
    await db.flush()
    return item


# --------------- Employee Metrics ---------------

async def list_employee_metrics(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    employee_id: UUID | None = None,
    period_type: str | None = None,
) -> tuple[list[EmployeeMetric], int]:
    stmt = select(EmployeeMetric)
    count_stmt = select(func.count()).select_from(EmployeeMetric)

    if employee_id:
        stmt = stmt.where(EmployeeMetric.employee_id == employee_id)
        count_stmt = count_stmt.where(EmployeeMetric.employee_id == employee_id)
    if period_type:
        stmt = stmt.where(EmployeeMetric.period_type == period_type)
        count_stmt = count_stmt.where(EmployeeMetric.period_type == period_type)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(EmployeeMetric.period_start.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_employee_metric(db: AsyncSession, metric_id: UUID) -> EmployeeMetric:
    result = await db.execute(select(EmployeeMetric).where(EmployeeMetric.id == metric_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Employee metric not found")
    return item


# --------------- Performance Reviews ---------------

async def list_performance_reviews(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    employee_id: UUID | None = None,
    status: str | None = None,
) -> tuple[list[PerformanceReview], int]:
    stmt = select(PerformanceReview)
    count_stmt = select(func.count()).select_from(PerformanceReview)

    if employee_id:
        stmt = stmt.where(PerformanceReview.employee_id == employee_id)
        count_stmt = count_stmt.where(PerformanceReview.employee_id == employee_id)
    if status:
        stmt = stmt.where(PerformanceReview.status == status)
        count_stmt = count_stmt.where(PerformanceReview.status == status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(PerformanceReview.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_performance_review(db: AsyncSession, review_id: UUID) -> PerformanceReview:
    result = await db.execute(select(PerformanceReview).where(PerformanceReview.id == review_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Performance review not found")
    return item


async def create_performance_review(
    db: AsyncSession, data: PerformanceReviewCreate, reviewer_id: UUID
) -> PerformanceReview:
    item = PerformanceReview(**data.model_dump(), reviewer_id=reviewer_id, status="draft")
    item.created_at = datetime.now(timezone.utc)
    db.add(item)
    await db.flush()
    return item


async def update_performance_review(
    db: AsyncSession, review_id: UUID, data: PerformanceReviewUpdate
) -> PerformanceReview:
    review = await get_performance_review(db, review_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(review, key, value)
    review.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return review


# --------------- Employee Goals ---------------

async def list_employee_goals(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    employee_id: UUID | None = None,
    status: str | None = None,
) -> tuple[list[EmployeeGoal], int]:
    stmt = select(EmployeeGoal)
    count_stmt = select(func.count()).select_from(EmployeeGoal)

    if employee_id:
        stmt = stmt.where(EmployeeGoal.employee_id == employee_id)
        count_stmt = count_stmt.where(EmployeeGoal.employee_id == employee_id)
    if status:
        stmt = stmt.where(EmployeeGoal.status == status)
        count_stmt = count_stmt.where(EmployeeGoal.status == status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(EmployeeGoal.period_end.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_employee_goal(db: AsyncSession, goal_id: UUID) -> EmployeeGoal:
    result = await db.execute(select(EmployeeGoal).where(EmployeeGoal.id == goal_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Employee goal not found")
    return item


async def create_employee_goal(db: AsyncSession, data: EmployeeGoalCreate, created_by: UUID) -> EmployeeGoal:
    item = EmployeeGoal(**data.model_dump(), created_by=created_by, status="active")
    item.created_at = datetime.now(timezone.utc)
    db.add(item)
    await db.flush()
    return item


async def update_employee_goal(db: AsyncSession, goal_id: UUID, data: EmployeeGoalUpdate) -> EmployeeGoal:
    goal = await get_employee_goal(db, goal_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(goal, key, value)
    # Auto-compute progress
    if goal.target_value and goal.target_value > 0:
        goal.progress_percentage = min(100.0, (goal.current_value or 0) / goal.target_value * 100)
    goal.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return goal


# --------------- Work Logs ---------------

async def list_work_logs(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    employee_id: UUID | None = None,
    activity_type: str | None = None,
) -> tuple[list[WorkLog], int]:
    stmt = select(WorkLog)
    count_stmt = select(func.count()).select_from(WorkLog)

    if employee_id:
        stmt = stmt.where(WorkLog.employee_id == employee_id)
        count_stmt = count_stmt.where(WorkLog.employee_id == employee_id)
    if activity_type:
        stmt = stmt.where(WorkLog.activity_type == activity_type)
        count_stmt = count_stmt.where(WorkLog.activity_type == activity_type)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(WorkLog.started_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def create_work_log(db: AsyncSession, data: WorkLogCreate) -> WorkLog:
    item = WorkLog(**data.model_dump())
    item.created_at = datetime.now(timezone.utc)
    db.add(item)
    await db.flush()
    return item


# --------------- Employee Patterns ---------------

async def list_employee_patterns(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    employee_id: UUID | None = None,
    is_active: bool | None = None,
) -> tuple[list[EmployeePattern], int]:
    stmt = select(EmployeePattern)
    count_stmt = select(func.count()).select_from(EmployeePattern)

    if employee_id:
        stmt = stmt.where(EmployeePattern.employee_id == employee_id)
        count_stmt = count_stmt.where(EmployeePattern.employee_id == employee_id)
    if is_active is not None:
        stmt = stmt.where(EmployeePattern.is_active == is_active)
        count_stmt = count_stmt.where(EmployeePattern.is_active == is_active)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(EmployeePattern.detected_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


# --------------- Schedules ---------------

async def list_employee_schedules(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    employee_id: UUID | None = None,
    status: str | None = None,
) -> tuple[list[EmployeeSchedule], int]:
    stmt = select(EmployeeSchedule)
    count_stmt = select(func.count()).select_from(EmployeeSchedule)

    if employee_id:
        stmt = stmt.where(EmployeeSchedule.employee_id == employee_id)
        count_stmt = count_stmt.where(EmployeeSchedule.employee_id == employee_id)
    if status:
        stmt = stmt.where(EmployeeSchedule.status == status)
        count_stmt = count_stmt.where(EmployeeSchedule.status == status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(EmployeeSchedule.effective_from.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_employee_schedule(db: AsyncSession, schedule_id: UUID) -> EmployeeSchedule:
    result = await db.execute(select(EmployeeSchedule).where(EmployeeSchedule.id == schedule_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Employee schedule not found")
    return item


async def create_employee_schedule(
    db: AsyncSession, data: EmployeeScheduleCreate, approved_by: UUID | None = None
) -> EmployeeSchedule:
    item = EmployeeSchedule(**data.model_dump(), approved_by=approved_by)
    item.created_at = datetime.now(timezone.utc)
    db.add(item)
    await db.flush()
    return item


async def update_employee_schedule(
    db: AsyncSession, schedule_id: UUID, data: EmployeeScheduleUpdate
) -> EmployeeSchedule:
    schedule = await get_employee_schedule(db, schedule_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(schedule, key, value)
    schedule.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return schedule


# --------------- Training Records ---------------

async def list_training_records(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    employee_id: UUID | None = None,
    status: str | None = None,
) -> tuple[list[TrainingRecord], int]:
    stmt = select(TrainingRecord)
    count_stmt = select(func.count()).select_from(TrainingRecord)

    if employee_id:
        stmt = stmt.where(TrainingRecord.employee_id == employee_id)
        count_stmt = count_stmt.where(TrainingRecord.employee_id == employee_id)
    if status:
        stmt = stmt.where(TrainingRecord.status == status)
        count_stmt = count_stmt.where(TrainingRecord.status == status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(TrainingRecord.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_training_record(db: AsyncSession, record_id: UUID) -> TrainingRecord:
    result = await db.execute(select(TrainingRecord).where(TrainingRecord.id == record_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Training record not found")
    return item


async def create_training_record(
    db: AsyncSession, data: TrainingRecordCreate, assigned_by: UUID
) -> TrainingRecord:
    item = TrainingRecord(**data.model_dump(), assigned_by=assigned_by, status="assigned")
    item.created_at = datetime.now(timezone.utc)
    db.add(item)
    await db.flush()
    return item


async def update_training_record(
    db: AsyncSession, record_id: UUID, data: TrainingRecordUpdate
) -> TrainingRecord:
    record = await get_training_record(db, record_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    record.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return record
