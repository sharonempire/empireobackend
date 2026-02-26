"""Analytics service — aggregated queries for the dashboard."""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.applications.models import Application
from app.modules.cases.models import VALID_STAGES, Case
from app.modules.employee_automation.models import EmployeeMetric
from app.modules.leads.models import Lead
from app.modules.students.models import Student
from app.modules.users.models import User

logger = logging.getLogger("empireo.analytics")


async def team_performance(db: AsyncSession, period_type: str = "weekly") -> dict:
    """Aggregate team performance from eb_employee_metrics for the latest period.

    Returns a TeamPerformanceSummary-compatible dict with:
      - period, period_start, period_end
      - total_employees, avg_performance_score, avg_quality_score
      - total_calls, total_cases_progressed, total_applications
      - top_performers (top 5 by ai_performance_score)
    """
    # Find the latest period_start for the given period_type
    latest_start_stmt = (
        select(func.max(EmployeeMetric.period_start))
        .where(EmployeeMetric.period_type == period_type)
    )
    latest_start_result = await db.execute(latest_start_stmt)
    latest_start = latest_start_result.scalar()

    if latest_start is None:
        return {
            "period": period_type,
            "period_start": None,
            "period_end": None,
            "total_employees": 0,
            "avg_performance_score": None,
            "avg_quality_score": None,
            "total_calls": 0,
            "total_cases_progressed": 0,
            "total_applications": 0,
            "top_performers": [],
        }

    # Aggregate metrics for all employees in that period
    agg_stmt = (
        select(
            func.count(func.distinct(EmployeeMetric.employee_id)).label("total_employees"),
            func.avg(EmployeeMetric.ai_performance_score).label("avg_performance_score"),
            func.avg(EmployeeMetric.ai_quality_score).label("avg_quality_score"),
            func.sum(EmployeeMetric.calls_made).label("total_calls"),
            func.sum(EmployeeMetric.cases_progressed).label("total_cases_progressed"),
            func.sum(EmployeeMetric.applications_submitted).label("total_applications"),
            func.max(EmployeeMetric.period_end).label("period_end"),
        )
        .where(EmployeeMetric.period_type == period_type)
        .where(EmployeeMetric.period_start == latest_start)
    )
    agg_result = await db.execute(agg_stmt)
    row = agg_result.one()

    # Find top 5 performers by ai_performance_score
    top_stmt = (
        select(
            EmployeeMetric.employee_id,
            EmployeeMetric.ai_performance_score,
            User.full_name,
        )
        .join(User, User.id == EmployeeMetric.employee_id)
        .where(EmployeeMetric.period_type == period_type)
        .where(EmployeeMetric.period_start == latest_start)
        .where(EmployeeMetric.ai_performance_score.is_not(None))
        .order_by(EmployeeMetric.ai_performance_score.desc())
        .limit(5)
    )
    top_result = await db.execute(top_stmt)
    top_rows = top_result.all()

    top_performers = [
        {
            "employee_id": str(r.employee_id),
            "name": r.full_name,
            "score": round(r.ai_performance_score, 2) if r.ai_performance_score else None,
        }
        for r in top_rows
    ]

    return {
        "period": period_type,
        "period_start": latest_start,
        "period_end": row.period_end,
        "total_employees": row.total_employees or 0,
        "avg_performance_score": round(row.avg_performance_score, 2) if row.avg_performance_score else None,
        "avg_quality_score": round(row.avg_quality_score, 2) if row.avg_quality_score else None,
        "total_calls": row.total_calls or 0,
        "total_cases_progressed": row.total_cases_progressed or 0,
        "total_applications": row.total_applications or 0,
        "top_performers": top_performers,
    }


async def conversion_funnel(db: AsyncSession) -> dict:
    """Count entities at each stage of the lead-to-visa conversion funnel.

    Returns a ConversionFunnel-compatible dict.
    """
    # Total leads
    leads_total_stmt = select(func.count()).select_from(Lead)
    leads_total = (await db.execute(leads_total_stmt)).scalar() or 0

    # Contacted leads (status is not 'new' and not null)
    leads_contacted_stmt = (
        select(func.count())
        .select_from(Lead)
        .where(Lead.status.is_not(None))
        .where(Lead.status != "new")
    )
    leads_contacted = (await db.execute(leads_contacted_stmt)).scalar() or 0

    # Students created
    students_stmt = select(func.count()).select_from(Student)
    students_created = (await db.execute(students_stmt)).scalar() or 0

    # Cases opened
    cases_stmt = select(func.count()).select_from(Case)
    cases_opened = (await db.execute(cases_stmt)).scalar() or 0

    # Applications submitted
    apps_stmt = select(func.count()).select_from(Application)
    applications_submitted = (await db.execute(apps_stmt)).scalar() or 0

    # Offers received (application status contains 'offer')
    offers_stmt = (
        select(func.count())
        .select_from(Application)
        .where(Application.status.ilike("%offer%"))
    )
    offers_received = (await db.execute(offers_stmt)).scalar() or 0

    # Offers accepted (cases at offer_accepted stage)
    accepted_stmt = (
        select(func.count())
        .select_from(Case)
        .where(Case.current_stage == "offer_accepted")
    )
    offers_accepted = (await db.execute(accepted_stmt)).scalar() or 0

    # Visas approved
    visa_stmt = (
        select(func.count())
        .select_from(Case)
        .where(Case.current_stage == "visa_approved")
    )
    visas_approved = (await db.execute(visa_stmt)).scalar() or 0

    return {
        "leads_total": leads_total,
        "leads_contacted": leads_contacted,
        "students_created": students_created,
        "cases_opened": cases_opened,
        "applications_submitted": applications_submitted,
        "offers_received": offers_received,
        "offers_accepted": offers_accepted,
        "visas_approved": visas_approved,
    }


async def case_velocity(db: AsyncSession) -> list[dict]:
    """Compute average days cases spend in each stage.

    Uses updated_at - created_at as a proxy for time spent in a stage.
    Groups by current_stage and calculates avg days.

    Returns a list of CaseVelocity-compatible dicts.
    """
    results = []

    for stage in VALID_STAGES:
        stmt = (
            select(
                func.count(Case.id).label("total_cases"),
                func.avg(
                    func.extract("epoch", Case.updated_at - Case.created_at) / 86400.0
                ).label("avg_days"),
            )
            .where(Case.current_stage == stage)
        )
        row = (await db.execute(stmt)).one()

        total_cases = row.total_cases or 0
        if total_cases == 0:
            continue

        avg_days = round(float(row.avg_days), 1) if row.avg_days is not None else 0.0

        results.append({
            "stage": stage,
            "avg_days": avg_days,
            "median_days": None,  # Median requires window functions; omitted for now
            "total_cases": total_cases,
        })

    return results


async def employee_trends(db: AsyncSession, employee_id: UUID, periods: int = 12) -> list[dict]:
    """Fetch the last N metric periods for an employee.

    Returns a list of EmployeeTrend-compatible dicts ordered by period_start ascending.
    """
    stmt = (
        select(EmployeeMetric)
        .where(EmployeeMetric.employee_id == employee_id)
        .order_by(EmployeeMetric.period_start.desc())
        .limit(periods)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    # Reverse so the list is ordered oldest-first
    rows = list(reversed(rows))

    return [
        {
            "period": f"{r.period_type}:{r.period_start.isoformat()}",
            "calls_made": r.calls_made or 0,
            "cases_progressed": r.cases_progressed or 0,
            "quality_score": round(r.avg_call_quality_score, 2) if r.avg_call_quality_score is not None else None,
            "performance_score": round(r.ai_performance_score, 2) if r.ai_performance_score is not None else None,
        }
        for r in rows
    ]


async def dashboard_summary(db: AsyncSession) -> dict:
    """Combined dashboard stats for the main dashboard."""
    from datetime import datetime, timedelta, timezone
    from app.modules.attendance.models import Attendance
    from app.modules.profiles.models import Profile

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # Lead stats
    total_leads = (await db.execute(select(func.count()).select_from(Lead))).scalar()
    fresh_leads = (await db.execute(
        select(func.count()).select_from(Lead).where(Lead.fresh.is_(True))
    )).scalar()
    backlog_leads = (await db.execute(
        select(func.count()).select_from(Lead).where(Lead.assigned_to.is_(None))
    )).scalar()

    # Lead counts by time period
    leads_today = (await db.execute(
        select(func.count()).select_from(Lead).where(Lead.created_at >= today_start)
    )).scalar()
    leads_this_week = (await db.execute(
        select(func.count()).select_from(Lead).where(Lead.created_at >= week_start)
    )).scalar()
    leads_this_month = (await db.execute(
        select(func.count()).select_from(Lead).where(Lead.created_at >= month_start)
    )).scalar()

    # Lead breakdown by status
    status_result = await db.execute(
        select(Lead.status, func.count()).group_by(Lead.status)
    )
    by_status = {row[0] or "unset": row[1] for row in status_result.all()}

    # Attendance today
    today_str = now.strftime("%Y-%m-%d")
    from sqlalchemy import text
    att_result = await db.execute(
        text("SELECT COUNT(*) FILTER (WHERE checkinat IS NOT NULL AND checkoutat IS NULL) AS checked_in, "
             "COUNT(*) FILTER (WHERE checkoutat IS NOT NULL) AS checked_out, "
             "COUNT(*) AS total_records "
             "FROM attendance WHERE date = :today"),
        {"today": today_str}
    )
    att_row = att_result.one()
    total_employees = (await db.execute(select(func.count()).select_from(Profile))).scalar()

    return {
        "leads": {
            "total": total_leads,
            "fresh": fresh_leads,
            "backlog": backlog_leads,
            "by_status": by_status,
        },
        "leads_today": leads_today,
        "leads_this_week": leads_this_week,
        "leads_this_month": leads_this_month,
        "attendance": {
            "checked_in": att_row[0],
            "checked_out": att_row[1],
            "not_checked_in": max(0, total_employees - att_row[2]),
            "total_employees": total_employees,
        },
    }
