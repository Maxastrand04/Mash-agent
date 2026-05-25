---
source: mash/main.py
test: behaviour-tests/0_fixtures.md
source_sha: 169929d
generated_sha: pending
---

# 0 — Fixtures & Constants

End-to-end behaviour tests for `mash`. Each scenario asserts the user-prompt → resolved `Run:` line via the CLI, isolating the program flow from LLM nondeterminism through dry-run plus stdin-fed menu selections.

## Constants

```
MASH="/Users/max/Documents/GitHub/Mash agent/.venv/bin/mash"
DIR="/Users/max/Documents/GitHub/Mash agent/Claude_testing"
```

Every invocation runs from `$DIR`:

```
cd "$DIR" && "$MASH" <flags> <prompt>
```

For interactive menus without `--yes`/`--dry-run`, feed input via stdin:

```
cd "$DIR" && printf '1\n' | "$MASH" <prompt>
```

## Phase 0 — Fixture reset

| # | Command | Status |
|---|---------|--------|
| 0.1 | `cd "$DIR" && find . -mindepth 1 -not -path "*/.*" -not -name "bugs_found.md" -delete` | ⬜ |
| 0.2 | `mkdir -p "$DIR/docs" "$DIR/reports" "$DIR/archive" "$DIR/tmp" "$DIR/src/deep/nested"` | ⬜ |
| 0.3 | `touch "$DIR/docs/overview.md" "$DIR/docs/notes.txt" "$DIR/archive/notes.txt" "$DIR/reports/summary.pdf" "$DIR/main.py" "$DIR/src/deep/nested/main.py" "$DIR/config.json" "$DIR/data.csv"` | ⬜ |
| 0.4 | `find "$DIR" -not -path "*/.*"` (verify tree) | ⬜ |

Two `notes.txt` (different folders), two `main.py` (root vs deep), one `reports/` dir, mixed file types.

## Agent: behaviour

**Job:** behaviour
**Targets:** fixture setup
**Cases:**
- Phase 0 fixture commands run to completion without error
- `find` output matches expected tree shape
