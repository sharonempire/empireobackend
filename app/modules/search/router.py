from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_perm
from app.modules.search import service
from app.modules.search.schemas import (
    DomainKeywordMapCreate,
    DomainKeywordMapOut,
    SearchSynonymCreate,
    SearchSynonymOut,
    StopwordCreate,
    StopwordOut,
)
from app.modules.users.models import User

router = APIRouter(prefix="/search-config", tags=["Search Config"])


@router.get("/domains", response_model=list[DomainKeywordMapOut])
async def api_list_domain_keywords(
    current_user: User = Depends(require_perm("search", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_domain_keywords(db)


@router.post("/domains", response_model=DomainKeywordMapOut, status_code=201)
async def api_create_domain_keyword(
    data: DomainKeywordMapCreate,
    current_user: User = Depends(require_perm("search", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_domain_keyword(db, data)
    await db.commit()
    return item


@router.get("/synonyms", response_model=list[SearchSynonymOut])
async def api_list_synonyms(
    current_user: User = Depends(require_perm("search", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_synonyms(db)


@router.post("/synonyms", response_model=SearchSynonymOut, status_code=201)
async def api_create_synonym(
    data: SearchSynonymCreate,
    current_user: User = Depends(require_perm("search", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_synonym(db, data)
    await db.commit()
    return item


@router.get("/stopwords", response_model=list[StopwordOut])
async def api_list_stopwords(
    current_user: User = Depends(require_perm("search", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_stopwords(db)


@router.post("/stopwords", response_model=StopwordOut, status_code=201)
async def api_create_stopword(
    data: StopwordCreate,
    current_user: User = Depends(require_perm("search", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_stopword(db, data)
    await db.commit()
    return item
