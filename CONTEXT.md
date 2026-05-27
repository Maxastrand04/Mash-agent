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
  mash_cli.py                      (class MashCLI)       — CLI entry point, top-level exception catch, verb dispatch
  intent.py                        (class Intent)        — @dataclass + @classmethod parse (pure, no I/O)
  exceptions/
    __init__.py
    mash_error.py                  (class MashError)
    user_cancelled.py              (class UserCancelled)
    source_not_found.py            (class SourceNotFound)
    destination_not_found.py       (class DestinationNotFound)
    llm_unavailable.py             (class LLMUnavailable)
    invalid_extension.py           (class InvalidExtension)
  helpers/
    __init__.py
    console.py                     (class Console)       — thin I/O: menus, prompts, yes/dry_run, confirm_and_run
    llm_client.py                  (class LLMClient)     — model, SYSTEM_PROMPT, ask; raises LLMUnavailable
    commands/
      __init__.py
      command_sanitizer.py         (class CommandSanitizer)   — pure @staticmethod command transforms
      command_templates.py         (class CommandTemplates)   — hardcoded bash templates
      command_reference.py         (class CommandReference)   — shell command reference list
    files/
      __init__.py
      extensions.py                (class Extensions)    — EXTENSION_MAP, collect, from_prompt, reconcile_rename
      path_resolver.py             (class PathResolver)  — resolve_paths, resolve_dirs (fuzzy matching)
      directory_context.py         (class DirectoryContext) — @classmethod get (directory tree string)
    selection/
      __init__.py
      disambiguator.py             (class Disambiguator) — pick_from_hits, pick_with_actions
      source_selector.py           (class SourceSelector)      — raises UserCancelled / SourceNotFound
      destination_selector.py      (class DestinationSelector) — raises UserCancelled / DestinationNotFound
      create_kind_picker.py        (class CreateKindPicker)    — raises UserCancelled
      extension_picker.py          (class ExtensionPicker)     — raises UserCancelled / InvalidExtension
      rename_extension_reconciler.py (class RenameExtensionReconciler) — raises UserCancelled
  flows/
    __init__.py
    move_copy_flow.py              (class MoveCopyFlow)
    rename_flow.py                 (class RenameFlow)
    delete_flow.py                 (class DeleteFlow)
    create_flow.py                 (class CreateFlow)
    open_cat_flow.py               (class OpenCatFlow)
    list_flow.py                   (class ListFlow)      — public entry point for list intent
    browse_mode.py                 (class BrowseMode)    — ls-and-menu loop
    action_menu.py                 (class ActionMenu)    — per-entry action picker
    list_scope.py                  (class ListScope)     — scoped context / list_entries / scope_label
scripts/
  check_conventions.py             (class ConventionChecker) — AC-1 + AC-3 AST checks
```

## Program flow

1. `MashCLI.main()` is the entry point (pyproject.toml `[project.scripts]`).
2. `MashCLI.run()` parses CLI args (`--yes`, `--dry-run`, remaining words), calls `_run_with_args`.
3. `_run_with_args` calls `Intent.parse(args)` — pure extraction, no I/O.
4. Collaborators are constructed with DI: `Console`, `LLMClient`, `Disambiguator`, selectors, pickers.
5. `_run_with_args` dispatches to the matching flow via verb (`if intent.verb == ...`).
6. Each flow orchestrates its lifecycle: source/dest selection, LLM call, command post-processing; returns a command string or `None`.
7. `MashCLI` calls `console.confirm_and_run(cmd)`.
8. `MashCLI.run` catches `LLMUnavailable` (friendly message + exit 1) and `MashError` (safety net).

## Layer responsibilities

- **`exceptions/`** — exception hierarchy only. No logic.
- **`Intent`** — pure data, no I/O. Extracts verb, args, dest_token, rename_target, create flags.
- **`Console`** — thin I/O boundary. Owns `yes`/`dry_run` flags. Raises `UserCancelled` when user declines.
- **`LLMClient`** — LLM boundary. Raises `LLMUnavailable` on failure.
- **`helpers/commands/`** — pure command transforms (`CommandSanitizer`) + reference data (`CommandTemplates`, `CommandReference`). All stateless (`@staticmethod` / `@classmethod`).
- **`helpers/files/`** — pure file logic (`Extensions`) + fuzzy matching (`PathResolver`) + directory tree (`DirectoryContext`). All stateless.
- **`helpers/selection/`** — source/destination selection business logic. Stateful (hold `Console` + `Disambiguator`). Raise named exceptions on cancel/not-found.
- **`flows/`** — per-intent orchestration. Stateful (hold all collaborators via DI). Each flow catches `UserCancelled` at its boundary and returns `None`.
- **`MashCLI`** — thin delegator + top-level safety net. No business logic.

## Import layers

Bottom to top: `exceptions/` → `intent.py` + `helpers/files/` + `helpers/commands/` → `helpers/console.py` + `helpers/llm_client.py` → `helpers/selection/` → `flows/` → `mash_cli.py`. Each layer imports only from layers below. No cycles.

## Naming and OOP conventions

**One class per file, file name matches class name.** Every `.py` under `mash/**` (excluding `__init__.py`) defines exactly one class. File name is the snake_case form of the class name.

**No abbreviations.** All identifiers use full descriptive words: `extension` not `ext`, `destination` not `dest`, `command` not `cmd`, `source` not `src`, `directory` not `dir`. Loop counters `i`/`j`/`k` and `*args`/`**kwargs` are allowed. Enforced via PR review; `scripts/check_conventions.py` enforces the OOP and sentinel-return rules automatically.

## Intentional behaviours

- **`create` flow** — single bare tokens (no extension, no path separator) intentionally fall through to the LLM / "give file a name" state rather than being auto-treated as filenames. Test agents have flagged this as a bug; it is deliberate.
- **`selection/destination`** — always renders a menu, even when there are 0 or 1 matches. No auto-return shortcut on low hit counts; the user is always given an explicit choice.
- **`pick_from_disambig`** (and the new `Disambig.pick_from_hits`) — always shows a menu regardless of hit count. Single-hit auto-selection is intentionally avoided so the user confirms the target.
- **`files/context`** — uses `find` only when building the directory context. A `tree`-first variant is a planned feature tracked as a separate work item, not a current bug.
