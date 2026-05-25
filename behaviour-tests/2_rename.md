---
source: mash/main.py
test: behaviour-tests/2_rename.md
source_sha: 169929d
generated_sha: pending
---

# 2 — Rename behaviour

| # | Command | Expected `Run:` line | Status |
|---|---------|----------------------|--------|
| 2.1 | `printf '1\n' \| --dry-run rename main.py to app.py` | `mv ./main.py ./app.py` (shallowest match) | ⬜ |
| 2.2 | `printf '1\n' \| --dry-run rename main.py app.py` (no "to") | same as 2.1 | ⬜ |
| 2.3 | `printf '1\ny\n' \| --dry-run rename overview.md to overview.txt` | extension change prompt shown; `mv ./docs/overview.md ./docs/overview.txt` | ⬜ |
| 2.4 | `printf '1\nn\n' \| --dry-run rename overview.md to overview.txt` | extension change prompt rejected; no `Run:` | ⬜ |
| 2.5 | `printf '1\n' \| --dry-run rename overview.md to summary` (bare name) | extension reconciled: `mv ./docs/overview.md ./docs/summary.md` | ⬜ |
| 2.6 | `--dry-run rename main.py to app.py 2>&1 \| grep -c "\[debug\]"` | `0` (no debug leak) | ⬜ |

## Agent: behaviour

**Job:** behaviour
**Targets:** rename intent + extension reconciliation
**Cases:**
- standard rename with disambig
- rename without "to" connective
- explicit extension change → prompt accepts
- explicit extension change → prompt rejects, no Run
- bare-name rename → extension preserved
- no debug output in user-facing stream
