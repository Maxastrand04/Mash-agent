---
source: mash/main.py
test: behaviour-tests/4_create.md
source_sha: 169929d
generated_sha: pending
---

# 4 — Create behaviour

| # | Command | Expected `Run:` line | Status |
|---|---------|----------------------|--------|
| 4.1 | `--dry-run create a python file called hello world` | `touch ./hello_world.py` | ⬜ |
| 4.2 | `--dry-run create a new directory called exports` | `mkdir -p ./exports` | ⬜ |
| 4.3 | `--dry-run create a new file called readme.txt` | `touch ./readme.txt` | ⬜ |
| 4.4 | `--dry-run create testing.pdf` (bare name with ext) | `touch ./testing.pdf` — no spurious destination | ⬜ |
| 4.5 | `printf '1\n1\n' \| --dry-run create drafts` (bare, no ext) | file/folder disambig + ext prompt; resolved Run uses chosen kind | ⬜ |
| 4.6 | `--dry-run create a python file called exports` (single token) | no format menu; `touch ./exports.py` | ⬜ |

## Agent: behaviour

**Job:** behaviour
**Targets:** create intent variants
**Cases:**
- multi-word name → snake_case normalization
- directory creation
- file creation with explicit extension
- bare name with extension → no destination prompt
- bare name without extension → file/folder + extension menus
- single-token name → format menu skipped
