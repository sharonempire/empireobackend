#!/bin/bash
# Extract JSON data from Supabase tool result files and combine into migration JSON files
set -e

RDIR="/Users/sharon/.claude/projects/-Users-sharon-empireobackend--claude-worktrees-silly-mcclintock/d5335ac6-bd9b-48f0-9c9a-1f75c6edb84d/tool-results"
ODIR="/Users/sharon/empireobackend/.claude/worktrees/silly-mcclintock/scripts/data"

mkdir -p "$ODIR"

extract_json() {
    # Given a tool result file, extract the row_to_json array
    local file="$1"
    jq -r '.[0].text' "$file" | jq -r '.' | grep -oP '(?<=<untrusted-data-[a-f0-9-]{36}>\n)\[.*\](?=\n</untrusted-data)' || \
    jq -r '.[0].text' "$file" | jq -r '.' | sed -n '/^\[{/,/}\]$/p'
}

extract_rows() {
    # Given a tool result file, extract just the inner objects from row_to_json wrappers
    local file="$1"
    jq -r '.[0].text' "$file" | jq -r '.' | sed -n '/^\[{/,/}\]$/p' | jq '[.[].row_to_json]'
}

# Function to identify table from a file
identify_table() {
    local file="$1"
    local sample_keys
    sample_keys=$(jq -r '.[0].text' "$file" | jq -r '.' | sed -n '/^\[{/,/}\]$/p' | jq -r '.[0].row_to_json | keys[]' 2>/dev/null | head -5 | tr '\n' ',')

    if echo "$sample_keys" | grep -q "heat_status"; then
        echo "leadslist"
    elif echo "$sample_keys" | grep -q "work_expierience\|english_proficiency"; then
        echo "lead_info"
    elif echo "$sample_keys" | grep -q "offer_details"; then
        echo "eb_applications"
    elif echo "$sample_keys" | grep -q "current_stage"; then
        echo "eb_cases"
    elif echo "$sample_keys" | grep -q "passport_number\|lead_id"; then
        echo "eb_students"
    else
        echo "unknown"
    fi
}

echo "Processing tool result files..."

# Process each file and group by table
declare -A TABLE_FILES

for file in "$RDIR"/mcp-claude_ai_Supabase-execute_sql-177208*.txt; do
    bn=$(basename "$file")
    table=$(identify_table "$file")
    echo "  $bn -> $table"

    if [ "$table" != "unknown" ]; then
        TABLE_FILES[$table]="${TABLE_FILES[$table]} $file"
    fi
done

echo ""

# For each table, combine files and write output
for table in leadslist lead_info eb_students eb_cases eb_applications; do
    files="${TABLE_FILES[$table]}"
    if [ -z "$files" ]; then
        echo "WARNING: No files found for $table"
        continue
    fi

    echo "Combining files for $table..."

    # Extract rows from each file and combine
    combined="[]"
    for file in $files; do
        rows=$(extract_rows "$file")
        if [ -n "$rows" ] && [ "$rows" != "null" ] && [ "$rows" != "[]" ]; then
            combined=$(echo "$combined" "$rows" | jq -s '.[0] + .[1]')
        fi
    done

    # Deduplicate by id
    combined=$(echo "$combined" | jq 'unique_by(.id)')

    # Sort by id
    combined=$(echo "$combined" | jq 'sort_by(.id)')

    count=$(echo "$combined" | jq 'length')

    echo "$combined" > "$ODIR/$table.json"
    size=$(wc -c < "$ODIR/$table.json")

    echo "  $table: $count rows, $size bytes -> $ODIR/$table.json"
done

echo ""
echo "Done! Files written:"
ls -la "$ODIR"/*.json
