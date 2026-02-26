"""
Fetch data from Supabase PostgreSQL and write to JSON files for migration.
Uses psycopg2 (sync) to connect directly and export each table as a JSON array.

Usage:
    python scripts/fetch_supabase_data.py
"""
import json
import os
import sys

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("psycopg2 not installed. Install with: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)

# Connection string (sync, from CLAUDE.md)
DATABASE_URL = "postgresql://postgres.ebgzlzemrargfahwokti:Empire%402025-2026@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")

# Tables to fetch: (table_name, output_filename, batch_size or None for single fetch)
TABLES = [
    ("chat_conversations", "chat_conversations.json", 1000),
    ("chat_messages", "chat_messages.json", None),
    ("payments", "payments.json", None),
    ("attendance", "attendance.json", None),
    ("notifications", "notifications.json", None),
    ("user_push_tokens", "user_push_tokens.json", None),
    ("user_fcm_tokens", "user_fcm_tokens.json", None),
]


def fetch_table(cursor, table_name, batch_size=None):
    """Fetch all rows from a table, optionally in batches."""
    all_rows = []

    if batch_size:
        offset = 0
        while True:
            query = f"SELECT row_to_json(t) AS data FROM {table_name} t ORDER BY id LIMIT {batch_size} OFFSET {offset}"
            cursor.execute(query)
            rows = cursor.fetchall()
            if not rows:
                break
            batch = [row[0] for row in rows]
            all_rows.extend(batch)
            print(f"  {table_name}: fetched {len(batch)} rows (offset {offset})", file=sys.stderr)
            offset += batch_size
            if len(batch) < batch_size:
                break
    else:
        query = f"SELECT row_to_json(t) AS data FROM {table_name} t ORDER BY id"
        cursor.execute(query)
        rows = cursor.fetchall()
        all_rows = [row[0] for row in rows]

    return all_rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Connecting to Supabase...", file=sys.stderr)
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    for table_name, filename, batch_size in TABLES:
        output_path = os.path.join(OUTPUT_DIR, filename)
        print(f"\nFetching {table_name}...", file=sys.stderr)
        try:
            rows = fetch_table(cursor, table_name, batch_size)
            with open(output_path, 'w') as f:
                json.dump(rows, f, indent=2, default=str)
            print(f"  Wrote {len(rows)} rows to {output_path}", file=sys.stderr)
        except Exception as e:
            print(f"  ERROR fetching {table_name}: {e}", file=sys.stderr)

    cursor.close()
    conn.close()
    print(f"\nDone!", file=sys.stderr)


if __name__ == "__main__":
    main()
