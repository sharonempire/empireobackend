from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
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

router = APIRouter(prefix="/search", tags=["Search"])


# ── Unified Search ────────────────────────────────────────────────────

@router.get("/")
async def api_unified_search(
    q: str = Query(..., min_length=1, description="Search query"),
    entity_type: str = Query("all", description="Entity type: all, course, lead, student, case, policy"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    use_ai: bool = Query(False, description="Use AI to parse natural language queries"),
    current_user: User = Depends(require_perm("search", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Hybrid search across all entities.

    Combines PostgreSQL full-text search (TSVECTOR), trigram similarity (fuzzy matching),
    and ILIKE substring matching. Results ranked by composite relevance score.

    Set `use_ai=true` to enable GPT-powered natural language query parsing,
    e.g. "hot leads from India interested in data science".
    """
    return await service.unified_search(db, q, entity_type, None, page, size, use_ai)


@router.get("/typeahead")
async def api_typeahead(
    q: str = Query(..., min_length=2, description="Autocomplete query"),
    entity_type: str = Query("all"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_perm("search", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Fast autocomplete/typeahead across entities.

    Returns top matches with trigram similarity scoring.
    Minimum 2 characters required.
    """
    return await service.typeahead(db, q, entity_type, limit)


# ── Search Config ─────────────────────────────────────────────────────

@router.get("/config/domains", response_model=list[DomainKeywordMapOut])
async def api_list_domain_keywords(
    current_user: User = Depends(require_perm("search", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_domain_keywords(db)


@router.post("/config/domains", response_model=DomainKeywordMapOut, status_code=201)
async def api_create_domain_keyword(
    data: DomainKeywordMapCreate,
    current_user: User = Depends(require_perm("search", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_domain_keyword(db, data)
    await log_event(db, "search_config.domain_created", current_user.id, "domain_keyword_map", str(item.id), {
        "domain": data.domain,
    })
    await db.commit()
    return item


@router.get("/config/synonyms", response_model=list[SearchSynonymOut])
async def api_list_synonyms(
    current_user: User = Depends(require_perm("search", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_synonyms(db)


@router.post("/config/synonyms", response_model=SearchSynonymOut, status_code=201)
async def api_create_synonym(
    data: SearchSynonymCreate,
    current_user: User = Depends(require_perm("search", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_synonym(db, data)
    await log_event(db, "search_config.synonym_created", current_user.id, "search_synonym", str(item.id), {
        "term": data.term,
    })
    await db.commit()
    return item


@router.get("/config/stopwords", response_model=list[StopwordOut])
async def api_list_stopwords(
    current_user: User = Depends(require_perm("search", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_stopwords(db)


@router.post("/config/stopwords", response_model=StopwordOut, status_code=201)
async def api_create_stopword(
    data: StopwordCreate,
    current_user: User = Depends(require_perm("search", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_stopword(db, data)
    await log_event(db, "search_config.stopword_created", current_user.id, "stopword", str(item.id), {
        "word": data.word,
    })
    await db.commit()
    return item
