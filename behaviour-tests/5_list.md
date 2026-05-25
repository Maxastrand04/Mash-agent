---
source: mash/main.py
test: behaviour-tests/5_list.md
source_sha: 169929d
generated_sha: pending
---

# 5 — List behaviour

| # | Command | Expected outcome | Status |
|---|---------|------------------|--------|
| 5.1 | `--dry-run list files in docs` | `Run: ls -la ./docs`; no source menu; no `[debug]` | ⬜ |
| 5.2 | `--dry-run list` (no target) | CWD listing or scope prompt | ⬜ |
| 5.3 | `printf '1\n1\n' \| --dry-run list files in docs` | action menu shown for first entry; resolved Run for chosen action | ⬜ |
| 5.4 | `printf '1\n2\n' \| --dry-run list files in docs` then rename action | rename path keeps extension via reconciliation | ⬜ |
| 5.5 | `printf '1\n3\ny\n' \| --dry-run list files in docs` then delete action | confirmation prompt shown before exec | ⬜ |
| 5.6 | List → fuzzy typed prompt → match | typed prompt resolves to a single entry | ⬜ |

## Agent: behaviour

**Job:** behaviour
**Targets:** list two-stage flow + action menu
**Cases:**
- plain listing of a folder
- list with no target
- list → action menu open
- list → rename action keeps extension
- list → delete action prompts confirmation
- list → typed-prompt fuzzy match
