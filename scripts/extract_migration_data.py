#!/usr/bin/env python3
"""
Extract leadslist, lead_info, eb_students, eb_cases, eb_applications
from persisted Supabase tool result files and write JSON for migration.

The tool result files are from queries run on 2026-02-26 ~10:43-10:45 UTC.
"""
import json
import re
import os
import glob
import sys

TOOL_RESULTS_DIR = "/Users/sharon/.claude/projects/-Users-sharon-empireobackend--claude-worktrees-silly-mcclintock/d5335ac6-bd9b-48f0-9c9a-1f75c6edb84d/tool-results"
OUTPUT_DIR = "/Users/sharon/empireobackend/.claude/worktrees/silly-mcclintock/scripts/data"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_rows_from_file(filepath):
    """Extract row_to_json objects from a persisted tool result file."""
    with open(filepath, "r") as f:
        content = f.read()

    # Parse outer JSON array
    outer = json.loads(content)
    if not outer or not isinstance(outer, list):
        return []

    # Get the text field
    text_raw = outer[0].get("text", "")

    # The text might be a JSON-encoded string or already a string
    if isinstance(text_raw, str):
        # Check if it's JSON-encoded (starts with a quote when it shouldn't)
        try:
            inner_text = json.loads(text_raw)
            if isinstance(inner_text, str):
                text = inner_text
            else:
                text = text_raw
        except (json.JSONDecodeError, TypeError):
            text = text_raw
    else:
        text = str(text_raw)

    # Extract the JSON array between untrusted-data tags
    match = re.search(
        r"<untrusted-data-[^>]+>\s*(\[.*?\])\s*</untrusted-data",
        text,
        re.DOTALL,
    )
    if not match:
        return []

    json_str = match.group(1)
    rows_raw = json.loads(json_str)

    # Extract the actual row objects
    rows = [r["row_to_json"] for r in rows_raw if "row_to_json" in r]
    return rows


def identify_table(keys):
    """Identify which table a row belongs to based on its columns."""
    key_set = set(keys)

    # leadslist: has heat_status, lead_tab, freelancer_manager
    if "heat_status" in key_set or "lead_tab" in key_set:
        return "leadslist"

    # lead_info: has work_expierience (typo), english_proficiency, interest_embedding
    if "work_expierience" in key_set or "english_proficiency" in key_set:
        return "lead_info"

    # eb_applications: has university_name + offer_details + case_id but NOT current_stage
    if "offer_details" in key_set and "university_name" in key_set:
        return "eb_applications"

    # eb_cases: has current_stage, case_type, student_id
    if "current_stage" in key_set and "case_type" in key_set:
        return "eb_cases"

    # eb_students: has lead_id, passport_number, counselor_id
    if "lead_id" in key_set and "passport_number" in key_set:
        return "eb_students"

    # Fallback: check for more flexible matches
    if "basic_info" in key_set and "education" in key_set:
        return "lead_info"

    if "student_id" in key_set and ("priority" in key_set or "visa_officer_id" in key_set):
        return "eb_cases"

    return None


def deduplicate_by_id(rows):
    """Deduplicate rows by id, keeping first occurrence."""
    seen = set()
    unique = []
    for row in rows:
        rid = str(row.get("id", ""))
        if rid and rid not in seen:
            seen.add(rid)
            unique.append(row)
        elif not rid:
            unique.append(row)
    return unique


def main():
    print("Extracting migration data from persisted tool results...")
    print(f"Looking in: {TOOL_RESULTS_DIR}")

    # Get all MCP result files
    all_files = sorted(
        glob.glob(os.path.join(TOOL_RESULTS_DIR, "mcp-claude_ai_Supabase-execute_sql-*.txt"))
    )
    print(f"Found {len(all_files)} total MCP result files\n")

    # Target tables
    tables = {
        "leadslist": [],
        "lead_info": [],
        "eb_students": [],
        "eb_cases": [],
        "eb_applications": [],
    }

    skipped = []

    for fpath in all_files:
        basename = os.path.basename(fpath)
        try:
            rows = extract_rows_from_file(fpath)
            if not rows:
                continue

            first = rows[0]
            keys = list(first.keys())
            table = identify_table(keys)

            if table and table in tables:
                tables[table].extend(rows)
                print(f"  {table:20s}: {basename} -> {len(rows)} rows")
            else:
                skipped.append((basename, len(rows), keys[:5]))
        except Exception as e:
            print(f"  ERROR: {basename}: {e}")

    if skipped:
        print(f"\nSkipped {len(skipped)} files (not matching target tables):")
        for name, count, sample_keys in skipped:
            print(f"  {name} ({count} rows, keys: {sample_keys})")

    # Deduplicate and write each table
    print("\n--- Writing output files ---")
    for table_name, rows in tables.items():
        unique_rows = deduplicate_by_id(rows)

        # Sort by id
        try:
            unique_rows.sort(key=lambda r: r.get("id", 0))
        except TypeError:
            # UUIDs vs ints
            unique_rows.sort(key=lambda r: str(r.get("id", "")))

        out_path = os.path.join(OUTPUT_DIR, f"{table_name}.json")
        with open(out_path, "w") as f:
            json.dump(unique_rows, f, indent=2, default=str)

        size = os.path.getsize(out_path)
        print(f"  {table_name:20s}: {len(unique_rows):>5} rows -> {out_path} ({size:>12,} bytes)")


if __name__ == "__main__":
    main()
