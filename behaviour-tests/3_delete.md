---
source: mash/main.py
test: behaviour-tests/3_delete.md
source_sha: 169929d
generated_sha: pending
---

# 3 — Delete behaviour

| # | Command | Expected `Run:` line | Status |
|---|---------|----------------------|--------|
| 3.1 | `printf '1\n' \| --dry-run delete notes.txt` | menu shows both notes.txt; `rm ./docs/notes.txt` | ⬜ |
| 3.2 | `printf '2\n' \| --dry-run delete notes.txt` | `rm ./archive/notes.txt` | ⬜ |
| 3.3 | `printf '\n' \| delete notes.txt` (blank) | menu shown; no `Run:` (cancel) | ⬜ |
| 3.4 | `printf '1\n' \| --dry-run delete reports` (folder) | `rm -rf ./reports` | ⬜ |
| 3.5 | `printf '1\ny\n' \| --yes delete summary.pdf` then `ls reports` | `summary.pdf` no longer present | ⬜ |

## Agent: behaviour

**Job:** behaviour
**Targets:** delete intent + confirmation flow
**Cases:**
- ambiguous source → menu pick #1
- ambiguous source → menu pick #2
- blank confirmation → cancels
- folder delete → recursive flag
- live `--yes` delete removes file from disk
