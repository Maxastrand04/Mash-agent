# Mash — Domain Glossary

## Intent

The action the user wants to perform, as classified by the LLM from the natural language query. Examples: move, copy, rename, delete, create file, create folder, list, open, cat, chmod.

The LLM's sole responsibility is to identify the intent and select the matching **Template**. It has no creative latitude — it does not construct commands, resolve paths, or make decisions beyond template selection.

## Template

A hardcoded bash command pattern corresponding to an intent (e.g. `move_file`, `delete_folder`). The LLM picks one; Python fills in the resolved paths.

## Query

The natural language string the user passes to `mash` (e.g. `move report.pdf to reports`).

## Source

An existing file or folder being operated on. Applies to: move, copy, rename, delete, open, cat, chmod. Not applicable to create actions.

## Destination

The directory the source is placed into, or the directory a new file/folder is created within.

## Resolution

The process of fuzzy-matching a token from the query against the directory tree (via `difflib`) to produce one or more candidate paths. Two variants:

- **Source resolution** — searches files and folders, used for all non-create actions.
- **Destination resolution** — searches directories only, used for move, copy, and create destination.

## Browse mode

The list action's interaction mode. Runs `ls -la` on the target directory, presents the contents as a disambiguation menu, then on selection shows an action menu (go into, add, rename, move, copy, remove, list contents, chmod — filtered by file vs folder). The selected item is pre-filled as the resolved source when routing into another flow.

Future scope: replace the action menu with a natural language follow-up prompt (user types what they want to do with the selected item, LLM classifies intent). Decision deferred to user settings phase.

## Extension reconciliation

A rename-specific sub-flow that runs after source resolution. Compares the old and new extension and prompts the user when they differ: keep old / use new / cancel. If the new name has no extension, the old extension is kept automatically.

## Extension picker

A create-specific sub-flow that fires whenever no extension can be inferred from the query. Presents a numbered list of extensions seen in the current directory tree plus a manual input option. Always runs for create actions with no extension — never skips to `touch` without one.

## Extension validation

A shared rule enforced by both extension reconciliation and the extension picker. Rejects manually typed extensions that are not real file extensions (e.g. `.nonexistingextension`). Applied whenever the user types an extension manually.

## Delete safety prompt

A delete-specific confirmation shown before the run confirmation. Displays the absolute path of the resolved source and asks the user to confirm before proceeding. Exists because deletion is irreversible. Skipped when `--yes` is active.

## Run confirmation

The final `[y/N]` prompt shown before mash executes a command. Always displays the exact shell command to be run. Distinct from the disambiguation menu (which resolves what to act on) and the delete safety prompt (which warns about destructiveness). Skipped when `--yes` is active.

## User

Two primary users: **developers** who know what they want but forget exact syntax, and **terminal-shy users** who want a guided shell experience. The interactive disambiguation menu design serves both — developers get a fast confirm loop, beginners get explicit paths and choices. A future setting to switch between interactive and non-interactive output modes is planned but out of current scope.

## Scope

Mash handles one action per invocation: one intent, one source, one destination, one confirmation. Chained or multi-step commands are permanently out of scope. The tool's design principle is single confirmed action — users who want to chain actions run mash multiple times.

## Model

The LLM used for intent classification. Currently hardcoded to `qwen2.5-coder:7b` via Ollama. User-selectable model configuration is planned as a pre-ship feature but is out of scope until then. Not a runtime flag.

## `--yes` flag

A development-only flag that auto-selects the first candidate in every disambiguation menu and skips all `[y/N]` confirmations including the delete safety prompt. Intended to speed up headless testing by Claude — not a user-facing feature. May be removed if it proves unhelpful for that purpose.

## `--dry-run` flag

A development-only flag that behaves like `--yes` (auto-selects first candidate) but prints the command without executing it. Short-circuits browse mode — no interactive menu, just prints the resolved `ls -la` command and exits. Not a user-facing feature.

## Command sanitisation

A deterministic post-processing pass that runs after the LLM responds, before the command is shown to the user. Enforces safety invariants: replaces intent labels with real verbs, strips unneeded `mkdir` segments, downgrades `rm -rf` → `rm` and `cp -r` → `cp` based on source type, and re-applies resolved paths to override LLM drift.

## Source type

A property of the resolved source detected from the filesystem. Values: `file`, `folder`, `unknown`. `unknown` applies when the path was not confirmed via resolution (e.g. LLM-constructed). Used to gate safety downgrades: `rm -rf` → `rm` and `cp -r` → `cp` when source type is `file` or `unknown`.

## Candidate

A path returned by resolution before the user confirms it via the disambiguation menu. Qualified forms — **candidate source** and **candidate destination** — are used when both appear in the same context and clarity requires it. After the user selects, the result is the **resolved source** or **resolved destination**.

## Disambiguation menu

The interactive numbered prompt mash shows whenever it needs the user to confirm or select a path. Covers all cases: single match, multiple matches, and not-found fallbacks. The number of options varies but the concept is the same.

## Target name

The new name in a rename, or the filename/folder name being created.

---

## Architecture

```
mash/
  __init__.py
  main.py                          — parse args, parse intent, dispatch to flow, confirm_and_run
  intent.py                        — Intent dataclass + parse_intent() factory (pure)
  helpers/
    __init__.py
    console.py                     — Console class (thin I/O: menus, prompts, yes/dry_run)
    llm.py                         — LLMClient class (model, SYSTEM_PROMPT, ask)
    commands/
      __init__.py                  — re-exports from submodules
      sanitize.py                  — pure command transforms
      templates.py                 — hardcoded bash templates (moved from mash/)
      reference.py                 — shell command reference list (was mash/commands.py)
    files/
      __init__.py                  — re-exports from submodules
      extension.py                 — EXTENSION_MAP, reconcile, collect, format (pure)
      resolver.py                  — resolve_paths, resolve_dirs (moved from mash/, unchanged)
      context.py                   — get_directory_context()
    selection/
      __init__.py                  — re-exports select_source, select_destination, _pick_from_disambig
      source.py                    — select_source (uses Console + resolver)
      destination.py               — select_destination (uses Console + resolver)
  flows/
    __init__.py                    — re-exports all flow functions
    move_copy.py                   — move/copy flow
    rename.py                      — rename flow
    delete.py                      — delete flow
    create.py                      — create flow
    list.py                        — list flow + scoped_context, list_entries, scope_label helpers
    open_cat.py                    — open/cat flow
```

## Program flow

1. `main.py` parses CLI args (`--yes`, `--dry-run`, remaining words).
2. `parse_intent(args)` returns an `Intent` dataclass — pure extraction, no I/O.
3. `main.py` builds `Console(yes, dry_run)`, `LLMClient()`, calls `get_directory_context()`.
4. `main.py` dispatches to the matching flow function based on `Intent.verb`.
5. Each flow orchestrates its lifecycle: source/dest selection, LLM call, post-processing with sanitize helpers, and returns a `str | None` (the final shell command).
6. `main.py` calls `console.confirm_and_run(cmd)`.

## Layer responsibilities

- **`Intent`** — pure data, no I/O. Extracts verb, args, dest_token, rename_target, create flags from CLI args.
- **`Console`** — thin I/O boundary. Owns `yes`/`dry_run` flags. Provides: render_menu, ask_input, confirm_yes_no, confirm_action, confirm_and_run, abs, cwd_label.
- **`LLMClient`** — LLM boundary. Holds model name, SYSTEM_PROMPT. Single `ask()` method.
- **`helpers/commands/`** — pure command transforms (sanitize) + reference data (templates, command list).
- **`helpers/files/`** — pure file logic (extensions, formatting) + resolver (fuzzy matching) + context (directory tree).
- **`helpers/selection/`** — source/destination selection business logic. Uses Console for I/O, resolver for matching.
- **`flows/`** — per-intent orchestration. Each flow owns its full lifecycle and returns a command string.
- **`main.py`** — thin delegator. No business logic.

## Import rules

- Sub-packages re-export through `__init__.py`.
- Consumers import from the package, not individual files.
- No module imports from `flows/` or `main.py` except `main.py` itself.
