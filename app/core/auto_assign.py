"""Smart counselor auto-assignment — mirrors Supabase Edge Function `eb-auto-assign` (v2).

Scoring algorithm:
  +30 points — counselor's countries[] includes the lead's country_preference
  -2 points  — per active case assigned to this counselor (workload penalty)
  +10 points — user has the 'counselor' role (role bonus)

Picks the counselor with the highest score. Falls back to round-robin if no
counselors match or scores tie.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("empireo.auto_assign")

COUNTRY_MATCH_BONUS = 30
WORKLOAD_PENALTY = 2
ROLE_BONUS = 10


async def score_counselors(
    db: AsyncSession,
    country_preference: list[str] | None = None,
) -> list[dict]:
    """Score all active counselors and return ranked list.

    Returns list of {user_id, full_name, score, active_cases, countries_matched}.
    """
    from app.modules.users.models import User, UserRole, Role
    from app.modules.cases.models import Case

    # Get all active users
    users_result = await db.execute(
        select(User).where(User.is_active.is_(True))
    )
    users = users_result.scalars().all()

    scored = []
    for user in users:
        score = 0
        countries_matched = []

        # Check if user has counselor role
        is_counselor = any(
            r.lower() in ("counselor", "manager", "admin") for r in user.roles
        )
        if is_counselor:
            score += ROLE_BONUS

        # Country match bonus
        user_countries = user.countries or []
        if country_preference and user_countries:
            # user.countries is JSONB (could be list of strings or dicts)
            user_country_names = set()
            for c in user_countries:
                if isinstance(c, str):
                    user_country_names.add(c.lower())
                elif isinstance(c, dict):
                    user_country_names.add(c.get("name", "").lower())

            for pref in country_preference:
                if pref.lower() in user_country_names:
                    score += COUNTRY_MATCH_BONUS
                    countries_matched.append(pref)

        # Workload penalty: count active cases
        case_count_result = await db.execute(
            select(func.count()).select_from(Case)
            .where(
                Case.is_active.is_(True),
                Case.assigned_counselor_id == user.id,
            )
        )
        active_cases = case_count_result.scalar() or 0
        score -= active_cases * WORKLOAD_PENALTY

        if is_counselor:  # Only include users with a counselor-like role
            scored.append({
                "user_id": user.id,
                "full_name": user.full_name,
                "score": score,
                "active_cases": active_cases,
                "countries_matched": countries_matched,
            })

    # Sort by score descending, then by active_cases ascending (tiebreaker: less busy first)
    scored.sort(key=lambda x: (-x["score"], x["active_cases"]))
    return scored


async def auto_assign_counselor(
    db: AsyncSession,
    country_preference: list[str] | None = None,
) -> UUID | None:
    """Pick the best counselor for a lead/student based on scoring.

    Returns the UUID of the best-match counselor, or None if no counselors available.
    """
    ranked = await score_counselors(db, country_preference)

    if not ranked:
        logger.warning("No counselors available for auto-assignment")
        return None

    best = ranked[0]
    logger.info(
        "Auto-assigned counselor %s (score=%d, cases=%d, countries=%s)",
        best["full_name"], best["score"], best["active_cases"], best["countries_matched"],
    )
    return best["user_id"]


async def auto_assign_student(
    db: AsyncSession,
    student_id: UUID,
    country_preference: list[str] | None = None,
) -> dict:
    """Auto-assign a counselor to a student and their active case.

    Returns {counselor_id, counselor_name, score} or {error}.
    """
    from app.modules.students.models import Student
    from app.modules.cases.models import Case

    # Get student
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        return {"error": "student_not_found"}

    # Use student's preferred countries if not explicitly provided
    if not country_preference and student.preferred_countries:
        country_preference = student.preferred_countries

    counselor_id = await auto_assign_counselor(db, country_preference)
    if not counselor_id:
        return {"error": "no_counselors_available"}

    # Assign to student
    student.assigned_counselor_id = counselor_id
    await db.flush()

    # Also assign to any active cases for this student
    cases_result = await db.execute(
        select(Case).where(Case.student_id == student_id, Case.is_active.is_(True))
    )
    cases = cases_result.scalars().all()
    for case in cases:
        case.assigned_counselor_id = counselor_id
    await db.flush()

    # Get counselor name for response
    from app.modules.users.models import User

    counselor_result = await db.execute(select(User).where(User.id == counselor_id))
    counselor = counselor_result.scalar_one_or_none()

    return {
        "student_id": str(student_id),
        "counselor_id": str(counselor_id),
        "counselor_name": counselor.full_name if counselor else "Unknown",
        "cases_assigned": len(cases),
    }
