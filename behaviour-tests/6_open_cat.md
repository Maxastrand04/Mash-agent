---
source: mash/main.py
test: behaviour-tests/6_open_cat.md
source_sha: 169929d
generated_sha: pending
---

# 6 — Open / Cat behaviour

| # | Command | Expected `Run:` line | Status |
|---|---------|----------------------|--------|
| 6.1 | `--dry-run open summary.pdf` | `open ./reports/summary.pdf` | ⬜ |
| 6.2 | `--dry-run cat overview.md` | `cat ./docs/overview.md` | ⬜ |
| 6.3 | `printf '1\n' \| --dry-run open notes.txt` (ambiguous) | menu; `open ./docs/notes.txt` | ⬜ |
| 6.4 | `printf '3\n' \| --dry-run open nonexistent.txt` | not-found menu → cancel; no `Run:` | ⬜ |
| 6.5 | `printf '2\nhello.md\n' \| --dry-run open nonexistent.md` | not-found menu → create routes into create_flow | ⬜ |
| 6.6 | `printf '1\noverview.md\n' \| --dry-run open nonexistant.md` | not-found menu → retype, resolves to overview.md | ⬜ |

## Agent: behaviour

**Job:** behaviour
**Targets:** open/cat intent + not-found menu
**Cases:**
- open single hit
- cat single hit
- ambiguous → menu pick
- not-found → cancel
- not-found → create
- not-found → retype
