---
source: mash/main.py
test: behaviour-tests/1_move_copy.md
source_sha: 169929d
generated_sha: pending
---

# 1 — Move / Copy behaviour

Run after [0_fixtures.md](0_fixtures.md).

| # | Command | Expected `Run:` line | Status |
|---|---------|----------------------|--------|
| 1.1 | `--dry-run move data.csv to the reports folder` | `mv ./data.csv ./reports/` | ⬜ |
| 1.2 | `--dry-run copy config.json to the archive folder` | `cp ./config.json ./archive/` | ⬜ |
| 1.3 | `printf '2\n' \| --dry-run move notes.txt to reports` (ambiguous source) | `mv` line uses second listed candidate | ⬜ |
| 1.4 | `--dry-run move foo into bar` (variant prep "into") | resolved `mv` with correct source/dest | ⬜ |
| 1.5 | `printf '1\n' \| --dry-run move data.csv` (missing destination) | destination menu shown; pick #1 honored | ⬜ |
| 1.6 | `--yes move data.csv to reports` then `ls reports` | `data.csv` present in `./reports/` | ⬜ |

## Agent: behaviour

**Job:** behaviour
**Targets:** move/copy intent → resolved Run line
**Cases:**
- happy path move, dry-run
- happy path copy, dry-run
- ambiguous source → menu selection honored
- variant phrasing ("into" instead of "to")
- missing destination → menu shown
- live `--yes` move mutates filesystem
