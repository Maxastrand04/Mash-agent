---
source: mash/main.py
test: behaviour-tests/8_llm_mixups.md
source_sha: 169929d
generated_sha: pending
---

# 8 — LLM mix-ups (post-processing wins)

Verifies that menu selections and intent parsing override LLM output. Hints to the LLM are advisory; `_apply_source`, `_apply_destination`, `_apply_filename` are the contract.

| # | Scenario | Expected outcome | Status |
|---|----------|------------------|--------|
| 8.1 | `printf '2\n' \| --dry-run delete notes.txt` (LLM may emit any path) | `Run:` uses second listed candidate exactly | ⬜ |
| 8.2 | `printf '2\n' \| --dry-run move data.csv to reports` with both `./reports` and `./tmp/reports` present | `Run:` ends with chosen destination, not LLM's | ⬜ |
| 8.3 | `--dry-run create a python file called hello world` | `Run:` uses `hello_world.py`, not LLM's variant | ⬜ |
| 8.4 | LLM emits unrelated verb (e.g. `ls` for a delete prompt) | intent parser overrides → `rm` command produced | ⬜ |
| 8.5 | LLM emits no command at all | flow falls back to template + post-processing, still produces `Run:` | ⬜ |
| 8.6 | `--dry-run move data.csv` with ollama unreachable | graceful error message; no Python traceback | ⬜ |

## Agent: behaviour

**Job:** behaviour
**Targets:** LLM-mixup resilience via post-processing
**Cases:**
- menu selection beats LLM source guess
- menu selection beats LLM destination guess
- filename normalization beats LLM variant
- intent parser overrides wrong verb
- empty LLM response → template fallback
- ollama unreachable → graceful failure
