---
source: mash/main.py
test: behaviour-tests/7_disambiguation.md
source_sha: 169929d
generated_sha: pending
---

# 7 — Disambiguation menus

| # | Command | Expected outcome | Status |
|---|---------|------------------|--------|
| 7.1 | `--dry-run delete notes.txt` (no input) | menu lists both notes.txt with absolute paths | ⬜ |
| 7.2 | `--dry-run rename main.py to app.py` (no input) | menu lists both main.py; shallowest (`./main.py`) appears at #1 | ⬜ |
| 7.3 | `printf '99\n1\n' \| --dry-run delete notes.txt` | out-of-range input re-prompts; #1 then honored | ⬜ |
| 7.4 | `printf '\n' \| --dry-run delete notes.txt` | blank cancels; no `Run:` | ⬜ |
| 7.5 | `--dry-run delete main` (short name) | source disambig triggered despite short term | ⬜ |
| 7.6 | `printf '1\n' \| --dry-run move data.csv to reports` (after `mkdir -p tmp/reports`) | dest menu lists both `reports` and `tmp/reports`; #1 honored; cleanup `rm -rf tmp/reports` | ⬜ |

## Agent: behaviour

**Job:** behaviour
**Targets:** disambiguation menus (source + destination)
**Cases:**
- source menu lists candidates with absolute paths
- shallowest match listed first
- out-of-range input re-prompts
- blank cancels
- short / fuzzy term still triggers menu
- destination menu disambiguates two same-named dirs
