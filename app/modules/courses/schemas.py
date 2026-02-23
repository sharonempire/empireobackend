from datetime import datetime

from pydantic import BaseModel


class CourseOut(BaseModel):
    id: int
    name: str | None = None
    university: str | None = None
    country: str | None = None
    program_level: str | None = None
    duration: str | None = None
    tuition_fee: str | None = None
    currency: str | None = None
    intake: str | None = None
    description: str | None = None
    requirements: str | None = None
    url: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
