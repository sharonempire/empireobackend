"""Schemas for the analytics dashboard module."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class TeamPerformanceSummary(BaseModel):
    """Aggregated team performance metrics for a given period."""

    model_config = ConfigDict(from_attributes=True)

    period: str
    period_start: date
    period_end: date
    total_employees: int
    avg_performance_score: float | None
    avg_quality_score: float | None
    total_calls: int
    total_cases_progressed: int
    total_applications: int
    top_performers: list[dict]  # [{employee_id, name, score}]


class ConversionFunnel(BaseModel):
    """Lead-to-visa conversion funnel counts."""

    model_config = ConfigDict(from_attributes=True)

    leads_total: int
    leads_contacted: int
    students_created: int
    cases_opened: int
    applications_submitted: int
    offers_received: int
    offers_accepted: int
    visas_approved: int


class CaseVelocity(BaseModel):
    """Average time spent in a given case stage."""

    model_config = ConfigDict(from_attributes=True)

    stage: str
    avg_days: float
    median_days: float | None = None
    total_cases: int


class EmployeeTrend(BaseModel):
    """Single-period performance trend data for an employee."""

    model_config = ConfigDict(from_attributes=True)

    period: str
    calls_made: int
    cases_progressed: int
    quality_score: float | None
    performance_score: float | None
