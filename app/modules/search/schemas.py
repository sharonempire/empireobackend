from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DomainKeywordMapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    domain: str | None = None
    keywords: list[str] | None = None
    created_at: datetime | None = None


class DomainKeywordMapCreate(BaseModel):
    domain: str
    keywords: list[str] | None = None


class SearchSynonymOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    term: str | None = None
    synonyms: list[str] | None = None
    created_at: datetime | None = None


class SearchSynonymCreate(BaseModel):
    term: str
    synonyms: list[str] | None = None


class StopwordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    word: str | None = None
    created_at: datetime | None = None


class StopwordCreate(BaseModel):
    word: str
