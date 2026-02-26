"""Analytics dashboard endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_perm
from app.modules.analytics import service
from app.modules.analytics.schemas import (
    CaseVelocity,
    ConversionFunnel,
    EmployeeTrend,
    TeamPerformanceSummary,
)
from app.modules.users.models import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/team-performance", response_model=TeamPerformanceSummary)
async def get_team_performance(
    period: str = Query("weekly", description="Period type: daily, weekly, or monthly"),
    user: User = Depends(require_perm("analytics", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated team performance metrics for the latest period."""
    return await service.team_performance(db, period_type=period)


@router.get("/conversion-funnel", response_model=ConversionFunnel)
async def get_conversion_funnel(
    user: User = Depends(require_perm("analytics", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get lead-to-visa conversion funnel counts."""
    return await service.conversion_funnel(db)


@router.get("/case-velocity", response_model=list[CaseVelocity])
async def get_case_velocity(
    user: User = Depends(require_perm("analytics", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get average time cases spend in each stage."""
    return await service.case_velocity(db)


@router.get("/employee/{employee_id}/trends", response_model=list[EmployeeTrend])
async def get_employee_trends(
    employee_id: UUID,
    periods: int = Query(12, ge=1, le=52, description="Number of periods to retrieve"),
    user: User = Depends(require_perm("analytics", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get performance trend data for a specific employee over the last N periods."""
    return await service.employee_trends(db, employee_id=employee_id, periods=periods)


@router.get("/dashboard")
async def get_dashboard_summary(
    current_user: User = Depends(require_perm("reports", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Combined dashboard stats: leads + attendance summary."""
    return await service.dashboard_summary(db)
