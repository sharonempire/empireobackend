"""Search service — unified cross-entity search + config CRUD."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.search_engine import hybrid_search, quick_search, ai_parse_query
from app.modules.search.models import DomainKeywordMap, SearchSynonym, Stopword
from app.modules.search.schemas import DomainKeywordMapCreate, SearchSynonymCreate, StopwordCreate


# ── Unified Search ────────────────────────────────────────────────────

# Entity search configs: table → (search_columns, tsvector_column, select_columns, label_column)
ENTITY_CONFIGS = {
    "course": {
        "table": "courses",
        "search_columns": ["program_name", "university", "country"],
        "tsvector": "search_vector",
        "label": "program_name",
    },
    "lead": {
        "table": "leadslist",
        "search_columns": ["name", "email"],
        "tsvector": None,
        "label": "name",
    },
    "student": {
        "table": "eb_students",
        "search_columns": ["full_name", "email", "phone"],
        "tsvector": None,
        "label": "full_name",
    },
    "case": {
        "table": "eb_cases",
        "search_columns": ["case_type", "current_stage"],
        "tsvector": None,
        "label": "case_type",
    },
    "policy": {
        "table": "eb_policies",
        "search_columns": ["title", "category", "content"],
        "tsvector": None,
        "label": "title",
    },
}


async def unified_search(
    db: AsyncSession,
    query: str,
    entity_type: str = "all",
    filters: dict[str, Any] | None = None,
    page: int = 1,
    size: int = 20,
    use_ai: bool = False,
) -> dict:
    """Search across one or all entity types with hybrid ranking.

    Returns {results: [{entity_type, items, total}], query_info: {...}}
    """
    query_info: dict[str, Any] = {"original_query": query, "ai_parsed": False}

    # Optional: AI query parsing for natural language
    if use_ai and len(query) > 10:
        try:
            parsed = await ai_parse_query(query)
            if parsed.get("search_terms"):
                query = parsed["search_terms"]
            if parsed.get("entity_type") and parsed["entity_type"] != "all":
                entity_type = parsed["entity_type"]
            if parsed.get("filters"):
                filters = {**(filters or {}), **parsed["filters"]}
            query_info["ai_parsed"] = True
            query_info["ai_interpretation"] = parsed
        except Exception:
            pass  # Fall back to raw query

    targets = (
        [entity_type] if entity_type != "all"
        else list(ENTITY_CONFIGS.keys())
    )

    results = []
    for target in targets:
        config = ENTITY_CONFIGS.get(target)
        if not config:
            continue

        items, total = await hybrid_search(
            db=db,
            table_name=config["table"],
            query=query,
            search_columns=config["search_columns"],
            tsvector_column=config["tsvector"],
            filters=filters if entity_type != "all" else None,
            page=page,
            size=min(size, 10) if entity_type == "all" else size,
        )

        results.append({
            "entity_type": target,
            "items": items,
            "total": total,
        })

    return {"results": results, "query_info": query_info}


async def typeahead(
    db: AsyncSession,
    query: str,
    entity_type: str = "all",
    limit: int = 10,
) -> list[dict]:
    """Fast autocomplete across entities. Returns [{id, label, score, entity_type}]."""
    if not query or len(query) < 2:
        return []

    targets = (
        [entity_type] if entity_type != "all"
        else list(ENTITY_CONFIGS.keys())
    )

    all_suggestions = []
    per_entity_limit = max(3, limit // len(targets)) if len(targets) > 1 else limit

    for target in targets:
        config = ENTITY_CONFIGS.get(target)
        if not config:
            continue

        suggestions = await quick_search(
            db=db,
            table_name=config["table"],
            query=query,
            search_columns=config["search_columns"],
            label_column=config["label"],
            limit=per_entity_limit,
        )
        for s in suggestions:
            s["entity_type"] = target
        all_suggestions.extend(suggestions)

    # Sort by score descending, take top N
    all_suggestions.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_suggestions[:limit]


# ── Config CRUD (unchanged) ──────────────────────────────────────────

async def list_domain_keywords(db: AsyncSession) -> list[DomainKeywordMap]:
    result = await db.execute(select(DomainKeywordMap).order_by(DomainKeywordMap.domain))
    return result.scalars().all()


async def create_domain_keyword(db: AsyncSession, data: DomainKeywordMapCreate) -> DomainKeywordMap:
    item = DomainKeywordMap(**data.model_dump())
    db.add(item)
    await db.flush()
    return item


async def list_synonyms(db: AsyncSession) -> list[SearchSynonym]:
    result = await db.execute(select(SearchSynonym).order_by(SearchSynonym.trigger))
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
