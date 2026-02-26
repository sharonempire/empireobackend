#!/usr/bin/env python3
"""
Import Supabase data from JSON files into local Postgres.

Reads JSON files from scripts/data/ and inserts into local Postgres
in FK-safe order. Handles conflicts with ON CONFLICT DO NOTHING.
Automatically skips columns that don't exist in the target table.

Usage (inside Docker):
    python scripts/import_supabase_data.py

Usage (outside Docker, with .env loaded):
    python scripts/import_supabase_data.py
"""

import json
import os
import sys
import time

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.database import sync_session_factory

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------
# Import order (FK-safe)
# ---------------------------------------------------------------------------
# Tables already seeded: profiles, eb_users, eb_roles, eb_permissions,
#                        eb_user_roles, eb_role_permissions
# We skip those. Everything else in FK order:

IMPORT_ORDER = [
    # Geography chain
    "countries",
    "cities",
    "universities",
    "campuses",
    # Reference
    "intakes",
    "eb_workflow_definitions",
    # Jobs chain
    "job_profiles",
    "jobs",
    "jobs_countries",
    # Courses
    "courses",
    "university_courses",
    "applied_courses",
    "applied_jobs",
    "saved_courses",
    "saved_jobs",
    "course_approval_requests",
    # Leads chain
    "leadslist",
    "lead_info",
    "lead_assignment_tracker",
    # Students chain
    "eb_students",
    "eb_cases",
    "eb_applications",
    # Comms
    "call_events",
    "chat_conversations",
    "chat_messages",
    # Attendance & payments
    "attendance",
    "payments",
    # Notifications
    "notifications",
    "user_push_tokens",
    "user_fcm_tokens",
    # Utility
    "short_links",
    "dm_templates",
    "conversation_sessions",
    "agent_endpoints",
    "commission",
    "freelancers",
    "freelance_managers",
    "search_synonyms",
    "stopwords",
    "domain_keyword_map",
    "user_profiles",
]


def load_json(table_name: str) -> list[dict] | None:
    """Load a JSON data file. Returns None if file doesn't exist."""
    path = os.path.join(DATA_DIR, f"{table_name}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return None


def quote_ident(name: str) -> str:
    """Quote a SQL identifier (column/table name)."""
    return f'"{name}"'


def to_pg_array(val: list) -> str:
    """Convert a Python list to a PostgreSQL TEXT[] literal."""
    elements = []
    for item in val:
        if item is None:
            elements.append("NULL")
        else:
            s = str(item).replace("\\", "\\\\").replace('"', '\\"')
            elements.append(f'"{s}"')
    return "{" + ",".join(elements) + "}"


def get_table_columns(session, table_name: str) -> set[str]:
    """Get the set of column names that actually exist in the DB table."""
    result = session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :tbl"
        ),
        {"tbl": table_name},
    )
    return {row[0] for row in result}


def get_array_columns(session, table_name: str) -> set[str]:
    """Get columns that are PostgreSQL arrays (TEXT[], etc.) for this table."""
    result = session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :tbl "
            "AND data_type = 'ARRAY'"
        ),
        {"tbl": table_name},
    )
    return {row[0] for row in result}


def get_jsonb_columns(session, table_name: str) -> set[str]:
    """Get columns that are JSON/JSONB for this table."""
    result = session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :tbl "
            "AND udt_name IN ('json', 'jsonb')"
        ),
        {"tbl": table_name},
    )
    return {row[0] for row in result}


def import_table(session, table_name: str, data: list[dict], batch_size: int = 500):
    """Import data into a table using batch INSERT ... ON CONFLICT DO NOTHING."""
    if not data:
        print(f"  [{table_name}] No data to import")
        return 0

    # Get actual DB columns — only insert into columns that exist
    db_columns = get_table_columns(session, table_name)
    if not db_columns:
        print(f"    Warning: table {table_name} not found in DB")
        return 0

    # Get array-type and jsonb columns so we can convert them properly
    array_cols = get_array_columns(session, table_name)
    jsonb_cols = get_jsonb_columns(session, table_name)

    # Collect all unique column names from JSON data
    json_columns = set()
    for row in data:
        json_columns.update(row.keys())

    # Only use columns that exist in BOTH the JSON data and the DB table
    columns = sorted(json_columns & db_columns)
    skipped_cols = json_columns - db_columns
    if skipped_cols:
        print(f"\n    (skipping {len(skipped_cols)} cols not in DB: {', '.join(sorted(skipped_cols)[:5])}{'...' if len(skipped_cols) > 5 else ''})")
        print(f"  [{table_name}] Importing {len(data)} rows ... ", end="", flush=True)

    col_list = ", ".join(quote_ident(c) for c in columns)
    param_list = ", ".join(f":{c}" for c in columns)

    sql = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({param_list}) ON CONFLICT DO NOTHING'

    imported = 0
    errors = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        for row in batch:
            params = {}
            for col in columns:
                val = row.get(col)
                if isinstance(val, list):
                    if col in array_cols:
                        params[col] = to_pg_array(val)
                    else:
                        params[col] = json.dumps(val)
                elif isinstance(val, dict):
                    params[col] = json.dumps(val)
                elif col in jsonb_cols and val is not None and not isinstance(val, str):
                    # Non-string scalars (int, float, bool) going into JSONB
                    params[col] = json.dumps(val)
                elif col in jsonb_cols and isinstance(val, str):
                    # Plain string going into JSONB — wrap as JSON string
                    params[col] = json.dumps(val)
                else:
                    params[col] = val
            try:
                session.execute(text(sql), params)
                imported += 1
            except Exception as e:
                session.rollback()
                errors += 1
                if errors <= 3:
                    print(f"\n    Warning: row error in {table_name}: {e.__class__.__name__}: {str(e)[:200]}")
                continue
        session.commit()

    if errors > 3:
        print(f"\n    ({errors} total errors, showing first 3)")

    return imported


def main():
    print("=" * 60)
    print("Empireo - Supabase -> Local Postgres Data Import")
    print("=" * 60)

    session = sync_session_factory()
    total_imported = 0
    total_skipped = 0
    total_tables = 0
    start_time = time.time()

    try:
        for table_name in IMPORT_ORDER:
            data = load_json(table_name)
            if data is None:
                print(f"  [{table_name}] SKIP (no JSON file)")
                total_skipped += 1
                continue

            if len(data) == 0:
                print(f"  [{table_name}] SKIP (empty)")
                total_skipped += 1
                continue

            print(f"  [{table_name}] Importing {len(data)} rows ... ", end="", flush=True)
            try:
                imported = import_table(session, table_name, data)
                print(f"OK ({imported} inserted)")
                total_imported += imported
                total_tables += 1
            except Exception as e:
                session.rollback()
                print(f"ERROR: {e.__class__.__name__}: {str(e)[:200]}")

        elapsed = time.time() - start_time
        print()
        print("=" * 60)
        print(f"Import complete in {elapsed:.1f}s!")
        print(f"  Tables imported: {total_tables}")
        print(f"  Tables skipped:  {total_skipped}")
        print(f"  Total rows:      {total_imported}")
        print("=" * 60)

    except Exception as exc:
        session.rollback()
        print(f"\n\nFATAL ERROR: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
