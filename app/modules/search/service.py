"""Search config service layer."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.search.models import DomainKeywordMap, SearchSynonym, Stopword
from app.modules.search.schemas import DomainKeywordMapCreate, SearchSynonymCreate, StopwordCreate


async def list_domain_keywords(db: AsyncSession) -> list[DomainKeywordMap]:
    result = await db.execute(select(DomainKeywordMap).order_by(DomainKeywordMap.domain))
    return result.scalars().all()


async def create_domain_keyword(db: AsyncSession, data: DomainKeywordMapCreate) -> DomainKeywordMap:
    item = DomainKeywordMap(**data.model_dump())
    db.add(item)
    await db.flush()
    return item


async def list_synonyms(db: AsyncSession) -> list[SearchSynonym]:
    result = await db.execute(select(SearchSynonym).order_by(SearchSynonym.term))
    return result.scalars().all()


async def create_synonym(db: AsyncSession, data: SearchSynonymCreate) -> SearchSynonym:
    item = SearchSynonym(**data.model_dump())
    db.add(item)
    await db.flush()
    return item


async def list_stopwords(db: AsyncSession) -> list[Stopword]:
    result = await db.execute(select(Stopword).order_by(Stopword.word))
    return result.scalars().all()


async def create_stopword(db: AsyncSession, data: StopwordCreate) -> Stopword:
    item = Stopword(**data.model_dump())
    db.add(item)
    await db.flush()
    return item
