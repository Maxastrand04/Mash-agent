#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")/../claude_testing/testing_folder" && pwd)"
MASH="/Users/max/Documents/GitHub/Mash agent/.venv/bin/mash"

run_mash() {
    local label="$1"; shift
    echo "=== $label ==="
    cd "$DIR"
    "$MASH" --dry-run --yes "$@" 2>&1 | grep -E "^Run: " || echo "(no command)"
    echo ""
}

run_mash "move_with_dest" move report.pdf to reports
run_mash "move_no_dest" move report.pdf
run_mash "copy" copy report.pdf to reports
run_mash "rename_same_ext" rename report.pdf to summary.pdf
run_mash "rename_diff_ext" rename report.pdf to summary.txt
run_mash "delete_file" delete report.pdf
run_mash "delete_folder" delete reports
run_mash "create_file_with_ext" create file called app.js
run_mash "create_file_no_ext" create file called utils
run_mash "create_folder" create folder called archive
run_mash "list" list
run_mash "open" open report.pdf
run_mash "cat" cat notes.txt
run_mash "chmod" chmod 755 main.py
