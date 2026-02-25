"""High-performance hybrid search engine.

Combines four PostgreSQL-native strategies for fast, intelligent search:

1. Full-text search (TSVECTOR + GIN index) — stemming, ranking, language-aware
2. Trigram similarity (pg_trgm) — typo tolerance, fuzzy matching
3. ILIKE fallback — simple substring for short queries
4. AI query understanding — GPT parses natural language into structured filters

All search runs inside PostgreSQL — no external search engines needed.
Results are ranked by a weighted composite score.
"""

import json
import logging
from typing import Any

from sqlalchemy import text, func, or_, and_, literal_column, case as sql_case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_key, get_cache, set_cache

logger = logging.getLogger("empireo.search")

# Synonym + stopword cache (loaded once, refreshed every 10 min)
_synonym_map: dict[str, list[str]] | None = None
_stopwords: set[str] | None = None


async def _load_search_config(db: AsyncSession) -> None:
    """Load synonyms and stopwords from DB into module-level cache."""
    global _synonym_map, _stopwords

    cached = await get_cache("empireo:search:config")
    if cached:
        _synonym_map = cached.get("synonyms", {})
        _stopwords = set(cached.get("stopwords", []))
        return

    from app.modules.search.models import SearchSynonym, Stopword
    from sqlalchemy import select

    syn_result = await db.execute(select(SearchSynonym))
    _synonym_map = {}
    for row in syn_result.scalars().all():
        if row.term and row.synonyms:
            _synonym_map[row.term.lower()] = [s.lower() for s in row.synonyms]

    stop_result = await db.execute(select(Stopword))
    _stopwords = {row.word.lower() for row in stop_result.scalars().all() if row.word}

    await set_cache("empireo:search:config", {
        "synonyms": _synonym_map,
        "stopwords": list(_stopwords),
    }, ttl=600)


def expand_query(query: str) -> str:
    """Expand a query using synonyms and remove stopwords.

    "data science courses" → "data science data-science machine-learning courses"
    """
    if not query:
        return query

    words = query.lower().split()
    expanded = []

    for word in words:
        if _stopwords and word in _stopwords:
            continue
        expanded.append(word)
        if _synonym_map and word in _synonym_map:
            expanded.extend(_synonym_map[word])

    return " ".join(expanded)


async def hybrid_search(
    db: AsyncSession,
    table_name: str,
    query: str,
    search_columns: list[str],
    tsvector_column: str | None = None,
    select_columns: str = "*",
    filters: dict[str, Any] | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    """Execute a hybrid search combining full-text, trigram, and ILIKE.

    Args:
        db: AsyncSession
        table_name: SQL table name (e.g. "courses", "leadslist")
        query: User search query
        search_columns: Column names to search with ILIKE/trigram
        tsvector_column: Column name of TSVECTOR column (if available)
        select_columns: Columns to SELECT (default "*")
        filters: Additional WHERE conditions as {column: value}
        page: Page number
        size: Page size

    Returns:
        (rows as dicts, total count)
    """
    await _load_search_config(db)

    # Check cache first
    ck = cache_key("search", table_name, query, str(filters), str(page), str(size))
    cached = await get_cache(ck)
    if cached:
        return cached["items"], cached["total"]

    expanded = expand_query(query)
    pattern = f"%{query}%"

    # Build WHERE conditions
    where_parts = []
    params: dict[str, Any] = {"query": query, "pattern": pattern, "expanded": expanded}

    if filters:
        for i, (col, val) in enumerate(filters.items()):
            if val is not None:
                pname = f"filter_{i}"
                where_parts.append(f"{col} = :{pname}")
                params[pname] = val

    # Build scoring expression — combine multiple signals
    score_parts = []

    # Signal 1: Full-text search via TSVECTOR (weight: 5x)
    if tsvector_column:
        ts_query = " & ".join(w for w in expanded.split() if w)
        if ts_query:
            params["ts_query"] = ts_query
            score_parts.append(
                f"(CASE WHEN {tsvector_column} @@ to_tsquery('english', :ts_query) "
                f"THEN ts_rank({tsvector_column}, to_tsquery('english', :ts_query)) * 5.0 "
                f"ELSE 0 END)"
            )

    # Signal 2: Trigram similarity on each search column (weight: 3x)
    for col in search_columns:
        score_parts.append(
            f"COALESCE(similarity({col}::text, :query), 0) * 3.0"
        )

    # Signal 3: Exact substring match bonus (weight: 2x)
    ilike_cases = []
    for col in search_columns:
        ilike_cases.append(f"{col}::text ILIKE :pattern")
    if ilike_cases:
        combined_ilike = " OR ".join(ilike_cases)
        score_parts.append(f"(CASE WHEN ({combined_ilike}) THEN 2.0 ELSE 0 END)")

    # Signal 4: Starts-with bonus (weight: 1.5x)
    starts_pattern = f"{query}%"
    params["starts_pattern"] = starts_pattern
    for col in search_columns[:1]:  # Only on primary column
        score_parts.append(
            f"(CASE WHEN {col}::text ILIKE :starts_pattern THEN 1.5 ELSE 0 END)"
        )

    if not score_parts:
        score_expr = "1"
    else:
        score_expr = " + ".join(score_parts)

    # Build filter WHERE clause
    filter_clause = ""
    if where_parts:
        filter_clause = "AND " + " AND ".join(where_parts)

    # Build search WHERE — must match at least one signal
    search_conditions = []
    if tsvector_column:
        ts_query = " & ".join(w for w in expanded.split() if w)
        if ts_query:
            search_conditions.append(f"{tsvector_column} @@ to_tsquery('english', :ts_query)")

    for col in search_columns:
        search_conditions.append(f"{col}::text ILIKE :pattern")
        search_conditions.append(f"similarity({col}::text, :query) > 0.1")

    search_where = " OR ".join(search_conditions) if search_conditions else "TRUE"

    # Count query
    count_sql = text(f"""
        SELECT COUNT(*) FROM {table_name}
        WHERE ({search_where}) {filter_clause}
    """)
    count_result = await db.execute(count_sql, params)
    total = count_result.scalar() or 0

    if total == 0:
        return [], 0

    # Main query — sorted by composite relevance score
    offset = (page - 1) * size
    params["limit"] = size
    params["offset"] = offset

    main_sql = text(f"""
        SELECT {select_columns},
               ({score_expr}) AS _relevance_score
        FROM {table_name}
        WHERE ({search_where}) {filter_clause}
        ORDER BY _relevance_score DESC, created_at DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """)

    result = await db.execute(main_sql, params)
    rows = [dict(row._mapping) for row in result.all()]

    # Remove the internal score column from results
    for row in rows:
        row.pop("_relevance_score", None)

    # Cache for 60 seconds
    await set_cache(ck, {"items": rows, "total": total}, ttl=60)

    return rows, total


async def quick_search(
    db: AsyncSession,
    table_name: str,
    query: str,
    search_columns: list[str],
    id_column: str = "id",
    label_column: str | None = None,
    limit: int = 10,
    filters: dict[str, Any] | None = None,
) -> list[dict]:
    """Fast autocomplete/typeahead search using trigram similarity.

    Returns [{id, label, score}] sorted by relevance. No pagination overhead.
    """
    if not query or len(query) < 2:
        return []

    pattern = f"%{query}%"
    params: dict[str, Any] = {"query": query, "pattern": pattern, "limit": limit}

    # Build filter conditions
    filter_parts = []
    if filters:
        for i, (col, val) in enumerate(filters.items()):
            if val is not None:
                pname = f"f_{i}"
                filter_parts.append(f"{col} = :{pname}")
                params[pname] = val

    filter_clause = ("AND " + " AND ".join(filter_parts)) if filter_parts else ""

    # Which column to use as label
    label_col = label_column or search_columns[0]

    # Combine trigram + ILIKE for speed
    match_conditions = []
    score_parts = []
    for col in search_columns:
        match_conditions.append(f"{col}::text ILIKE :pattern")
        match_conditions.append(f"similarity({col}::text, :query) > 0.15")
        score_parts.append(f"COALESCE(similarity({col}::text, :query), 0)")

    match_where = " OR ".join(match_conditions)
    score_expr = " + ".join(score_parts) if score_parts else "0"

    sql = text(f"""
        SELECT {id_column} AS id,
               {label_col}::text AS label,
               ({score_expr}) AS score
        FROM {table_name}
        WHERE ({match_where}) {filter_clause}
        ORDER BY score DESC
        LIMIT :limit
    """)

    result = await db.execute(sql, params)
    return [dict(row._mapping) for row in result.all()]


async def ai_parse_query(query: str) -> dict:
    """Use GPT to parse a natural language query into structured filters + search terms.

    "show me hot leads from India interested in data science" →
    {
        "search_terms": "data science",
        "entity_type": "lead",
        "filters": {"heat_status": "hot", "country_preference": "India"},
        "intent": "search"
    }
    """
    from app.core.openai_service import chat_completion

    result = await chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "You parse search queries for a study abroad CRM system. "
                    "Extract structured filters and search terms. Return JSON:\n"
                    '{"search_terms": "cleaned keywords", "entity_type": "lead|student|course|case|policy|all", '
                    '"filters": {"field": "value"}, "intent": "search|filter|count|export"}\n\n'
                    "Known filter fields:\n"
                    "- Leads: status, heat_status (hot/warm/cold), assigned_to, country_preference, lead_tab\n"
                    "- Students: counselor_id, nationality, education_level\n"
                    "- Courses: country, program_level, university, field_of_study\n"
                    "- Cases: current_stage, is_active, case_type\n"
                    "- Policies: category, department, is_active\n\n"
                    "Return ONLY valid JSON. If no filters apply, return empty filters {}."
                ),
            },
            {"role": "user", "content": query},
        ],
        model="gpt-4o-mini",
        temperature=0.1,
        json_mode=True,
    )

    try:
        parsed = json.loads(result["content"])
        parsed["_tokens_used"] = result.get("tokens_used", 0)
        return parsed
    except (json.JSONDecodeError, KeyError):
        return {
            "search_terms": query,
            "entity_type": "all",
            "filters": {},
            "intent": "search",
        }
