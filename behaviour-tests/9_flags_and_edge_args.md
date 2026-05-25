---
source: mash/main.py
test: behaviour-tests/9_flags_and_edge_args.md
source_sha: 169929d
generated_sha: pending
---

# 9 — Flags & edge args

| # | Command | Expected outcome | Status |
|---|---------|------------------|--------|
| 9.1 | `--yes create a directory called sandbox` then `ls` | no confirmation prompt; `sandbox/` exists on disk | ⬜ |
| 9.2 | `--dry-run move data.csv to reports` | `Run:` printed; filesystem unchanged | ⬜ |
| 9.3 | (no args) | usage message printed; exit code non-zero | ⬜ |
| 9.4 | `polish the silver` (unknown intent) | fallthrough message or error; no destructive command | ⬜ |
| 9.5 | `--dry-run rename main.py to app.py 2>&1 \| grep -c "\[debug\]"` | `0` (no debug leak) | ⬜ |
| 9.6 | `--yes --dry-run delete notes.txt` (both flags) | dry-run wins: no exec, `Run:` printed | ⬜ |
| 9.7 | very long prompt (>500 chars) | parsed without crash; sensible Run or graceful failure | ⬜ |

## Agent: behaviour

**Job:** behaviour
**Targets:** CLI flags + edge argument handling
**Cases:**
- `--yes` skips confirmation
- `--dry-run` prints Run, no exec
- empty args → usage
- unknown intent → graceful fallthrough
- no `[debug]` lines in user output
- conflicting flags → dry-run takes precedence
- very long prompt → no crash
