from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NextActionSuggestion(BaseModel):
    suggested_action: str
    action_type: str  # stage_transition, send_notification, follow_up, etc.
    reason: str
    urgency: str  # high, medium, low
    draft_message: str | None = None
    confidence: float  # 0.0-1.0
    payload: dict = {}  # ready-to-use ActionDraft payload

    model_config = ConfigDict(from_attributes=True)


class LeadScoreResult(BaseModel):
    lead_id: int
    score: int  # 0-100
    heat_status: str  # hot, warm, cold
    factors: list[str]
    recommended_action: str

    model_config = ConfigDict(from_attributes=True)


class CaseNextStep(BaseModel):
    case_id: UUID
    current_stage: str
    suggested_next_stage: str
    reason: str
    blockers: list[str]
    estimated_days: int | None = None

    model_config = ConfigDict(from_attributes=True)


class EmailDraft(BaseModel):
    subject: str
    body: str
    tone: str
    suggested_attachments: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class EmailDraftRequest(BaseModel):
    entity_type: str  # "student" or "lead"
    entity_id: str
    email_type: str  # follow_up, offer_congrats, docs_request, payment_reminder
