#!/usr/bin/env python3
"""Extract table data from persisted Supabase tool result files and write JSON."""
import json
import re
import os
import glob

TOOL_RESULTS_DIR = "/Users/sharon/.claude/projects/-Users-sharon-empireobackend--claude-worktrees-silly-mcclintock/d5335ac6-bd9b-48f0-9c9a-1f75c6edb84d/tool-results"
OUTPUT_DIR = "/Users/sharon/empireobackend/.claude/worktrees/silly-mcclintock/scripts/data"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_data_from_file(filepath):
    """Extract data from a persisted tool result file. Handles both row_to_json and json_agg formats."""
    with open(filepath, "r") as f:
        content = f.read()

    outer = json.loads(content)
    if not outer or not isinstance(outer, list):
        return []

    text = outer[0].get("text", "")
    inner_text = json.loads(text)

    match = re.search(
        r"<untrusted-data-[^>]+>\n(\[.*?\])\n</untrusted-data",
        inner_text,
        re.DOTALL,
    )
    if not match:
        return []

    json_str = match.group(1)
    rows_raw = json.loads(json_str)

    # Handle row_to_json format: [{"row_to_json": {...}}, ...]
    if rows_raw and isinstance(rows_raw[0], dict) and "row_to_json" in rows_raw[0]:
        return [r["row_to_json"] for r in rows_raw if "row_to_json" in r]

    # Handle json_agg format: [{"json_agg": [...]}]
    if rows_raw and isinstance(rows_raw[0], dict) and "json_agg" in rows_raw[0]:
        agg = rows_raw[0]["json_agg"]
        if isinstance(agg, str):
            return json.loads(agg)
        return agg if agg else []

    # Direct array of objects
    if rows_raw and isinstance(rows_raw[0], dict):
        return rows_raw

    return []


def identify_table(rows):
    """Identify which table the rows belong to based on column signatures."""
    if not rows:
        return "unknown"
    first = rows[0]
    keys = set(first.keys())

    # university_courses has unique columns
    if "source_key" in keys or "university_image" in keys or "tuition_fee_international_annual" in keys:
        return "university_courses"

    # courses has program_name and many columns (55+)
    if "program_name" in keys and len(keys) > 25:
        return "courses"

    # applied_courses: has user_id, course_id, course_details, status, applied_at
    if "course_details" in keys and "applied_at" in keys and "course_id" in keys:
        return "applied_courses"

    # saved_courses: has user_id, course_id, course_details but no applied_at
    if "course_details" in keys and "course_id" in keys and "applied_at" not in keys:
        return "saved_courses"

    # applied_jobs: has job_details, job_id, candidate_name or job_title
    if "job_details" in keys and "job_id" in keys and ("candidate_name" in keys or "job_title" in keys):
        return "applied_jobs"

    # saved_jobs: has job_details, job_id but no candidate_name/job_title
    if "job_details" in keys and "job_id" in keys:
        return "saved_jobs"

    return "unknown"


def deduplicate_by_id(rows):
    """Deduplicate rows by id, keeping first occurrence."""
    seen = set()
    unique = []
    for row in rows:
        rid = row.get("id")
        rid_str = str(rid)
        if rid_str not in seen:
            seen.add(rid_str)
            unique.append(row)
    return unique


def main():
    print("Extracting data from persisted tool results...")

    all_files = sorted(
        glob.glob(os.path.join(TOOL_RESULTS_DIR, "*.txt"))
        + glob.glob(os.path.join(TOOL_RESULTS_DIR, "*.json"))
    )

    print(f"Found {len(all_files)} total files")

    table_data = {
        "courses": [],
        "university_courses": [],
        "applied_courses": [],
        "saved_courses": [],
        "applied_jobs": [],
        "saved_jobs": [],
    }

    for fpath in all_files:
        try:
            rows = extract_data_from_file(fpath)
            if not rows:
                continue
            table = identify_table(rows)
            if table in table_data:
                table_data[table].extend(rows)
                print(f"  {table}: {os.path.basename(fpath)} -> {len(rows)} rows")
            else:
                first = rows[0]
                print(f"  SKIP: {os.path.basename(fpath)} -> {len(rows)} rows, table={table}, keys={list(first.keys())[:8]}")
        except Exception as e:
            pass  # Skip files that don't parse

    # Deduplicate and sort
    for table in table_data:
        table_data[table] = deduplicate_by_id(table_data[table])
        try:
            table_data[table].sort(key=lambda r: r.get("id", 0))
        except TypeError:
            pass  # UUIDs and ints can't be compared, that's fine

    # Write output files
    for table, rows in table_data.items():
        out_path = os.path.join(OUTPUT_DIR, f"{table}.json")
        with open(out_path, "w") as f:
            json.dump(rows, f, indent=2, default=str)
        print(f"\nWrote {table}.json ({len(rows)} rows)")


if __name__ == "__main__":
    main()
