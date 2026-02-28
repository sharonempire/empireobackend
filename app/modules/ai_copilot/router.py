from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.ai_copilot.schemas import (
    CaseNextStep,
    EmailDraft,
    EmailDraftRequest,
    LeadScoreResult,
    NextActionSuggestion,
)
from app.modules.ai_copilot.service import (
    draft_email,
    score_lead,
    suggest_case_next_step,
    suggest_next_action,
)
from app.modules.users.models import User

router = APIRouter(prefix="/ai-copilot", tags=["AI Copilot"])


@router.get("/students/{student_id}/next-action", response_model=NextActionSuggestion)
async def api_suggest_next_action(
    student_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Suggest the best next action for a student based on AI analysis."""
    return await suggest_next_action(db, student_id)


@router.get("/leads/{lead_id}/score", response_model=LeadScoreResult)
async def api_score_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Score a lead based on profile completeness and engagement signals."""
    return await score_lead(db, lead_id)


@router.get("/cases/{case_id}/next-step", response_model=CaseNextStep)
async def api_suggest_case_next_step(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Suggest the next stage transition for a case."""
    return await suggest_case_next_step(db, case_id)


@router.post("/email-draft", response_model=EmailDraft)
async def api_draft_email(
    data: EmailDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an AI-powered email draft for a student or lead."""
    result = await draft_email(db, data.entity_type, data.entity_id, data.email_type)
    await log_event(db, "ai_copilot.email_drafted", current_user.id, data.entity_type, str(data.entity_id), {
        "email_type": data.email_type,
    })
    await db.commit()
    return result
