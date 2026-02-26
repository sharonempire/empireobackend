"""
Extract row_to_json results from Supabase MCP tool output files
and write them as clean JSON arrays.

Usage:
    python extract_sql_result.py <input_file> [output_file]
    python extract_sql_result.py --merge <output_file> <input_file1> <input_file2> ...
    python extract_sql_result.py --scan <results_dir> <output_dir>
"""
import json
import re
import sys
import os
import glob


def extract_rows(filepath):
    """Extract row_to_json results from Supabase tool output file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Try parsing as JSON wrapper first
    try:
        wrapper = json.loads(content)
        if isinstance(wrapper, list) and len(wrapper) > 0 and isinstance(wrapper[0], dict) and 'text' in wrapper[0]:
            text = wrapper[0]['text']
            # The text field might be a JSON string itself
            if isinstance(text, str) and text.startswith('"'):
                text = json.loads(text)
        elif isinstance(wrapper, str):
            text = wrapper
        else:
            text = content
    except Exception:
        text = content

    # If text is still a string, look for the JSON array in it
    if isinstance(text, str):
        match = re.search(r'\[\{.*\}\]', text, re.DOTALL)
        if match:
            arr_str = match.group(0)
            arr = json.loads(arr_str)
            rows = []
            for item in arr:
                if 'row_to_json' in item:
                    rows.append(item['row_to_json'])
                elif 'json_build_object' in item:
                    obj = item['json_build_object']
                    if 'rows' in obj and isinstance(obj['rows'], list):
                        rows.extend(obj['rows'])
                    else:
                        rows.append(obj)
                else:
                    rows.append(item)
            return rows

    return []


def identify_table(filepath):
    """Identify which table a result file contains by checking for unique column names."""
    with open(filepath, 'r') as f:
        snippet = f.read(3000)

    # Table signature patterns - unique column/value names in each table
    sigs = [
        ('chat_conversations', 'counselor_id'),
        ('chat_messages', 'message_text'),
        ('payments', 'razorpay'),
        ('attendance', 'checkinat'),
        ('notifications', 'notification_type'),
        ('user_push_tokens', 'push_token'),
        ('user_fcm_tokens', 'fcm_token'),
    ]
    for table, sig in sigs:
        if sig in snippet:
            return table
    return None


def scan_and_group(results_dir, output_dir):
    """Scan all result files, identify tables, group batches, and write output."""
    files = sorted(
        glob.glob(os.path.join(results_dir, 'mcp-claude_ai_Supabase-execute_sql-*.txt')),
        key=os.path.getmtime,
        reverse=True
    )

    # Also check .json files (persisted output format)
    json_files = sorted(
        glob.glob(os.path.join(results_dir, 'toolu_*.json')),
        key=os.path.getmtime,
        reverse=True
    )

    table_files = {}  # table_name -> list of (timestamp, filepath)

    for f in files[:40]:  # Check most recent 40 files
        table = identify_table(f)
        if table:
            ts = os.path.basename(f).replace('mcp-claude_ai_Supabase-execute_sql-', '').replace('.txt', '')
            if table not in table_files:
                table_files[table] = []
            table_files[table].append((ts, f))
            print(f"  Found {table} in {os.path.basename(f)} ({os.path.getsize(f)} bytes)", file=sys.stderr)

    for f in json_files[:20]:
        table = identify_table(f)
        if table:
            if table not in table_files:
                table_files[table] = []
            table_files[table].append(('json', f))
            print(f"  Found {table} in {os.path.basename(f)} ({os.path.getsize(f)} bytes)", file=sys.stderr)

    os.makedirs(output_dir, exist_ok=True)

    for table, file_list in table_files.items():
        # Sort by timestamp (newest first) and take all unique files
        all_rows = []
        seen_ids = set()

        for ts, fp in sorted(file_list, key=lambda x: x[0]):
            rows = extract_rows(fp)
            for row in rows:
                row_id = row.get('id', id(row))
                if row_id not in seen_ids:
                    seen_ids.add(row_id)
                    all_rows.append(row)

        output_path = os.path.join(output_dir, f'{table}.json')
        with open(output_path, 'w') as out:
            json.dump(all_rows, out, indent=2, default=str)
        print(f"  {table}: {len(all_rows)} unique rows -> {output_path}", file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == '--merge':
        # Merge mode: combine multiple files into one
        output_path = sys.argv[2]
        input_files = sys.argv[3:]
        all_rows = []
        for f in input_files:
            rows = extract_rows(f)
            print(f"  {f}: {len(rows)} rows", file=sys.stderr)
            all_rows.extend(rows)
        with open(output_path, 'w') as out:
            json.dump(all_rows, out, indent=2, default=str)
        print(f"Wrote {len(all_rows)} total rows to {output_path}", file=sys.stderr)

    elif len(sys.argv) >= 3 and sys.argv[1] == '--scan':
        results_dir = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else '.'
        print(f"Scanning {results_dir}...", file=sys.stderr)
        scan_and_group(results_dir, output_dir)
        print("Done!", file=sys.stderr)

    else:
        filepath = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        rows = extract_rows(filepath)
        result = json.dumps(rows, indent=2, default=str)
        if output_path:
            with open(output_path, 'w') as f:
                f.write(result)
            print(f"Wrote {len(rows)} rows to {output_path}", file=sys.stderr)
        else:
            print(result)
        print(f"ROW COUNT: {len(rows)}", file=sys.stderr)
