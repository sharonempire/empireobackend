"""Lead intake pipeline — mirrors Supabase Edge Function `eb-lead-intake` (v2).

Full pipeline:
1. Create lead in leadslist (DB triggers: duplicate blocking, phone normalization,
   round-robin assignment, fresh flag, lead_info row, chat conversation)
2. Create eb_student record (DB trigger: auto-creates eb_case)
3. Smart auto-assign counselor (country-based scoring from eb-auto-assign)
4. Update lead with assigned counselor
5. Return complete intake result

This replaces the multi-step Edge Function with a single backend endpoint
that leverages both DB triggers and Python business logic.
"""

import logging
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auto_assign import auto_assign_counselor

logger = logging.getLogger("empireo.lead_intake")


async def run_lead_intake(
    db: AsyncSession,
    intake_data: dict[str, Any],
) -> dict[str, Any]:
    """Execute the full lead intake pipeline.

    Args:
        db: Async database session
        intake_data: Dict with lead data:
            - name: str (required)
            - email: str | None
            - phone: int | None
            - source: str | None (e.g., "website", "instagram", "referral", "walk-in")
            - country_preference: list[str] | None
            - lead_tab: str (default "student")
            - basic_info: dict | None (for lead_info)
            - education: dict | None (for lead_info)
            - budget_info: dict | None (for lead_info)
            - preferences: dict | None (for lead_info)

    Returns:
        Dict with all created entity IDs and assignment info.
    """
    result: dict[str, Any] = {"success": False, "steps": []}

    try:
        # ─── Step 1: Create lead ─────────────────────────────────
        # DB triggers handle: duplicate blocking, phone normalization,
        # round-robin assignment, fresh flag, lead_info row, chat conversation
        from app.modules.leads.models import Lead, LeadInfo

        lead = Lead(
            name=intake_data.get("name"),
            email=intake_data.get("email"),
            phone=intake_data.get("phone"),
            source=intake_data.get("source", "website"),
            status="Lead creation",
            heat_status="warm",
            lead_tab=intake_data.get("lead_tab", "student"),
            country_preference=intake_data.get("country_preference"),
        )
        db.add(lead)
        await db.flush()
        await db.refresh(lead)
        result["lead_id"] = lead.id
        result["steps"].append({"step": "create_lead", "status": "ok", "lead_id": lead.id})
        logger.info("Intake: Created lead %d", lead.id)

        # ─── Step 2: Update lead_info with detailed data ─────────
        # The ensure_lead_info_row trigger already created the row
        lead_info_result = await db.execute(
            select(LeadInfo).where(LeadInfo.id == lead.id)
        )
        lead_info = lead_info_result.scalar_one_or_none()

        if lead_info:
            if intake_data.get("basic_info"):
                lead_info.basic_info = intake_data["basic_info"]
            if intake_data.get("education"):
                lead_info.education = intake_data["education"]
            if intake_data.get("budget_info"):
                lead_info.budget_info = intake_data["budget_info"]
            if intake_data.get("preferences"):
                lead_info.preferences = intake_data["preferences"]
            if intake_data.get("english_proficiency"):
                lead_info.english_proficiency = intake_data["english_proficiency"]
            if intake_data.get("domain_tags"):
                lead_info.domain_tags = intake_data["domain_tags"]
            await db.flush()
            result["steps"].append({"step": "update_lead_info", "status": "ok"})
        else:
            result["steps"].append({"step": "update_lead_info", "status": "skipped", "reason": "no_lead_info_row"})

        # ─── Step 3: Create eb_student ───────────────────────────
        # DB trigger on eb_students auto-creates an eb_case
        from app.modules.students.models import Student

        student = Student(
            lead_id=lead.id,
            full_name=intake_data.get("name", "Unknown"),
            email=intake_data.get("email"),
            phone=str(intake_data.get("phone")) if intake_data.get("phone") else None,
            preferred_countries=intake_data.get("country_preference"),
        )

        # Copy education details if provided
        if intake_data.get("education"):
            edu = intake_data["education"]
            student.education_level = edu.get("level")
            student.education_details = edu

        db.add(student)
        await db.flush()
        await db.refresh(student)
        result["student_id"] = str(student.id)
        result["steps"].append({"step": "create_student", "status": "ok", "student_id": str(student.id)})
        logger.info("Intake: Created student %s for lead %d", student.id, lead.id)

        # ─── Step 4: Smart auto-assign counselor ─────────────────
        # Uses the scoring algorithm from eb-auto-assign Edge Function
        country_preference = intake_data.get("country_preference", [])
        counselor_id = await auto_assign_counselor(db, country_preference)

        if counselor_id:
            # Update student
            student.assigned_counselor_id = counselor_id
            # Update lead
            lead.assigned_to = counselor_id
            await db.flush()

            # Also update the auto-created case
            from app.modules.cases.models import Case

            case_result = await db.execute(
                select(Case).where(Case.student_id == student.id, Case.is_active.is_(True))
            )
            case = case_result.scalar_one_or_none()
            if case:
                case.assigned_counselor_id = counselor_id
                await db.flush()
                result["case_id"] = str(case.id)

            # Get counselor name
            from app.modules.users.models import User

            counselor_result = await db.execute(select(User).where(User.id == counselor_id))
            counselor = counselor_result.scalar_one_or_none()

            result["counselor_id"] = str(counselor_id)
            result["counselor_name"] = counselor.full_name if counselor else "Unknown"
            result["steps"].append({
                "step": "auto_assign",
                "status": "ok",
                "counselor_id": str(counselor_id),
                "counselor_name": counselor.full_name if counselor else "Unknown",
            })
            logger.info("Intake: Assigned counselor %s to lead %d", counselor_id, lead.id)
        else:
            result["steps"].append({"step": "auto_assign", "status": "skipped", "reason": "no_counselors"})
            logger.warning("Intake: No counselors available for lead %d", lead.id)

        # ─── Step 5: Verify chat conversation was created ────────
        # The ensure_chat_conversation_for_lead trigger should have created one
        if counselor_id:
            chat_result = await db.execute(
                text("""
                    SELECT id FROM chat_conversations
                    WHERE lead_uuid = :lead_uuid
                    ORDER BY created_at DESC LIMIT 1
                """),
                {"lead_uuid": str(lead.id)},
            )
            chat_row = chat_result.first()
            if chat_row:
                result["chat_conversation_id"] = chat_row[0]
                result["steps"].append({"step": "chat_conversation", "status": "ok"})
            else:
                result["steps"].append({"step": "chat_conversation", "status": "skipped"})

        result["success"] = True
        logger.info("Intake pipeline completed for lead %d", lead.id)

    except Exception as e:
        logger.error("Intake pipeline failed: %s", e)
        result["success"] = False
        result["error"] = str(e)

    return result
