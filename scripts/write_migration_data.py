#!/usr/bin/env python3
"""
Write migration data JSON files from inline Supabase query results.
Each table's raw MCP output is stored as a string, parsed, and written.

Run: python3 scripts/write_migration_data.py
"""
import json
import re
import os

OUT = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT, exist_ok=True)

def extract(raw: str) -> list[dict]:
    """Parse MCP output text and return list of row dicts."""
    m = re.search(r'<untrusted-data-[^>]+>\n(.*?)\n</untrusted-data', raw, re.DOTALL)
    if not m:
        raise ValueError("No untrusted-data block found")
    rows = json.loads(m.group(1))
    return [r["row_to_json"] for r in rows]

def write_json(name: str, data: list[dict]):
    path = os.path.join(OUT, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  {name}.json: {len(data)} rows")

# Raw MCP outputs will be passed via the calling script
if __name__ == "__main__":
    print("Use this module's extract() and write_json() functions.")
