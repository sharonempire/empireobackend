from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CallEventOut(BaseModel):
    id: int
    created_at: datetime | None = None
    event_type: str | None = None
    call_uuid: str | None = None
    caller_number: str | None = None
    called_number: str | None = None
    agent_number: str | None = None
    call_status: str | None = None
    total_duration: int | None = None
    conversation_duration: int | None = None
    call_start_time: datetime | None = None
    call_end_time: datetime | None = None
    recording_url: str | None = None
    dtmf: str | None = None
    transferred_number: str | None = None
    destination: str | None = None
    callerid: str | None = None
    call_date: str | None = None
    extension: str | None = None
    caller_phone_norm: str | None = None
    agent_phone_norm: str | None = None

    model_config = ConfigDict(from_attributes=True)
