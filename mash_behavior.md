# Mash Behavior Cheat Sheet

Quick reference for how `mash` interprets each type of user action, what it asks, and what command it runs.

Flags: `--yes`/`-y` and `--dry-run` are development-only testing aids (not user-facing). See Flag behavior section.

---

## Universal prompt template

All disambiguation prompts follow the same shape:

```
Mash found <thing(s)> for '<token>':

  1. <first option / only option>
  2. <next option>
  ...

Select option [1-N], Enter to cancel, type name for other file/folder:
```

The footer has two variants:
- **Source / list / file-or-folder pickers:** `Select option [1-N], Enter to cancel, type name for other file/folder:` — the typed input is interpreted as a new search term against the directory tree.
- **Destination prompts (create / move / copy destination, including not-found and no-destination fallbacks):** `Select option [1-N], Enter to cancel, type name for other destination:` — the typed input is interpreted as a destination retype (a new search term against the directories only).

For "not found" cases the header reads: `Mash did not find <thing>, choose how to proceed:` and the menu includes the available fallbacks (e.g. `create ./<token>`, `select <cwd>`).

**Path entries in every menu are shown as absolute paths** (e.g. `/Users/max/Documents/GitHub/Mash agent/report.pdf`). This applies uniformly to:
- single-match source menus,
- multi-match source menus,
- destination menus (single and multi-match),
- create-destination menus (found and not-found branches),
- `<cwd>` entries (rendered as the full current-directory path, not `./`).

The rule: any time mash displays a file or folder option to the user, it is shown as an absolute path so the user can immediately see where on disk it lives.

**Current-directory annotation:** in every destination menu (mv/cp destination, create-file destination, create-folder destination — both found and not-found branches), the entry that represents the current working directory is suffixed with `(Current directory)` so the user can recognise it at a glance. Example: `/Users/max/Documents/GitHub/Mash agent  (Current directory)`.

---

## Move (file or folder)

**Trigger words:** `move`, plus optional `to`/`into`/`inside`/`in <dest>`.

**Example:** `mash move report.pdf to reports`

**Flow:**
1. Fuzzy-resolves source from args (skipping stop words / dest token).
2. Disambiguation menu (source) — even a single candidate uses the numbered template. Each entry shows the **absolute path** so the user knows exactly where on disk the match lives:
   ```
   Mash found a file for 'report':

     1. /Users/max/Documents/GitHub/Mash agent/report.pdf

   Select option [1], Enter to cancel, type name for other file/folder:
   ```
   Multiple matches → same shape with `[1-N]`.
3. Detects source type (file, folder, or unknown) from filesystem.
4. Disambiguation menu (destination) — same template. Single candidate still uses `[1]`. Multiple → `[1-N]`. Not found → menu with `create ./<token>` and `select <cwd>`.
5. **No destination given** (e.g. `mash move report.pdf`, or move triggered from the list action menu without `to <dest>`): mash MUST prompt with a menu listing the current directory as the default option — never fall back to the literal token `unknown`.
   ```
   Where should this be moved? Choose a destination:

     1. /Users/max/Documents/GitHub/Mash agent  (Current directory)

   Select option [1], Enter to cancel, type destination:
   ```
   Typing a name re-runs the destination search; Enter cancels.
6. LLM picks `move_file` or `move_folder` template.
7. Run confirmation `[y/N]` then execute.

**Command:** `mv <source> <destination>/`

---

## Copy (file or folder)

**Trigger words:** `copy`, `duplicate`, `clone`, `replicate`, plus optional destination marker.

**Example:** `mash copy notes.md into archive`

**Flow:** identical to move — source uses the numbered menu template (even for one match), then destination uses the same template (even for one match). Not-found destination → menu with `create ./<token>` / `select <cwd>`. **No destination given** → same fallback menu as move (option 1 = current directory, `Select option [1], Enter to cancel, type destination:`).

**Safety:** if source type is `file` or `unknown`, `cp -r` is stripped to `cp`.

**Command:** `cp <source> <destination>/` or `cp -r <source> <destination>/`

---

## Rename (file or folder)

**Trigger phrases:** `rename`, `change name`, `alter name`, `swap name`, `relabel`, `rebrand`, `retitle`, `reassign name`, `give new name`. New name follows the last `to` after the verb.

**Example:** `mash rename oldfile.txt to newfile.txt`

**Flow:**
1. Detects rename verb and extracts the token after `to`.
2. Disambiguation menu (source) — same template.
3. Destination marker before the rename verb is allowed (combine: move + rename).
4. **Extension reconciliation** (MUST apply in every code path that reaches rename — direct CLI, browse mode action menu, etc.):
   - New name has no ext, old has one → auto-keeps old ext.
   - Same ext → no prompt.
   - Different ext → prompts: keep old / use new / cancel.
   - Old had none, new adds one → prompts: keep none / add new / cancel.
5. Run confirmation `[y/N]` then execute.

**Command:** `mv <before> <after>` or `mv <before> <dest>/<after>`

---

## Delete (file or folder)

**Trigger words:** `delete`, `remove`.

**Example:** `mash delete tempfile.log`

**Flow:**
1. Disambiguation menu (source) — same template.
2. Detects source type (file, folder, or unknown).
3. LLM picks `delete_file` (`rm`) or `delete_folder` (`rm -rf`).
4. **Safety:** if source type is `file` or `unknown`, `rm -rf` is downgraded to `rm`.
5. **Delete safety prompt** (before the run confirmation), formatted to match the disambiguation menu layout (header, indented path, prompt on its own line):
   ```
   Are you sure you want to delete:

      /Users/Max/path/to/file.extension

   [y/N] :
   ```
   The path is the absolute path of the resolved source. `N` / Enter cancels.
6. Run confirmation `[y/N]` then execute.

**Command:** `rm <path>` or `rm -rf <path>`

---

## Create file

**Trigger:** starts with `create` or `make`. The word `file` is **optional** — if the argument looks like a filename (contains `.`, e.g. `testing.pdf`), or `called`/`named` is used with an extension hint, mash treats it as create-file.

**Examples:**
- `mash create file called user profile`
- `mash create testing.pdf` ← destination prompt MUST still run for this shape.

**Flow:**
1. Parses name tokens after `called`/`named`. Needs **≥ 2 tokens** to trigger the filename formatter.
2. Extension comes from a token like `foo.py` or from a language word (`python`, `markdown`, `js`, …). **If none → ALWAYS run the extension picker** (numbered list of extensions seen in the tree, or manual input). This rule applies in every entry point — direct CLI (`mash create file called foo`), bare CLI (`mash create foo`), or routed from browse mode's `add` action with a single-token name like `apple`. Mash MUST NOT run `touch ./apple` without an extension.
3. Offers three formats: `snake_case`, `kebab-case`, `camelCase`. Manual name also accepted.
4. **Destination flow** (for create) — **always runs**, regardless of whether the user typed `to`/`into`/`inside`/`in <dest>`. All branches use the universal menu template:
   - **No destination mentioned** → "Where should the new file be created?" with `<cwd>` as option 1. This branch MUST fire for shapes like `mash create testing.pdf` where the create intent was inferred without an explicit destination marker.
   - **Mentioned + found:**
     ```
     Mash found a folder for '<token>':

       1. /Users/max/Documents/GitHub/Mash agent/reports
       2. /Users/max/Documents/GitHub/Mash agent  (Current directory)

     Select option [1-2], Enter to cancel, type name for other destination:
     ```
     Typing another name re-runs the search.
   - **Mentioned + not found:**
     ```
     Mash did not find directory '<token>', choose how to proceed:

       1. select /Users/max/Documents/GitHub/Mash agent  (Current directory)
       2. create /Users/max/Documents/GitHub/Mash agent/<token>

     Select option [1-2], Enter to cancel, type name for other destination:
     ```
     Typing another name re-runs the search.
5. If the destination must be created, command becomes `mkdir -p <dest> && touch <dest>/<file>`.
6. Run confirmation `[y/N]` then execute.

**Command:** `touch ./<name>` or `touch <dest>/<name>`

---

## Create folder / directory

**Trigger:** starts with `create`/`make`, contains `folder`/`directory`/`dir`.

**Example:** `mash create folder called drafts in reports`

**Flow:** same destination flow as create file (all branches via the universal menu). No extension prompt. Filename formatter only fires if the name has ≥ 2 tokens after `called`/`named`.

**Command:** `mkdir -p <dest>/<name>` or `mkdir -p ./<name>`

---

## Browse mode

**Trigger words:** `list`, `ls`, `show files`, `show contents`.

**Example:** `mash list all files`

**Flow:**
0. **`--dry-run` short-circuit:** under `--dry-run` the list flow does NOT enter the interactive menu. It resolves the target path the same way and prints `Run: ls -la <resolved>` + `[dry-run] command not executed.`, preserving the universal `--dry-run` contract. `--yes` (without `--dry-run`) still enters the interactive flow and auto-selects option 1.
1. Default target is the current directory unless the user explicitly names another path (e.g. `mash list files in reports`).
2. **Header path is relative to cwd.** The header uses `.` for cwd and `./<subdir>` for a subdirectory — never the absolute path. Entry rows still show absolute paths.
   ```
   Mash listing .:

     1. /Users/max/Documents/GitHub/Mash agent/mash  (folder)
     2. /Users/max/Documents/GitHub/Mash agent/implementation_plans  (folder)
     3. /Users/max/Documents/GitHub/Mash agent/mash_behavior.md
     4. /Users/max/Documents/GitHub/Mash agent/pyproject.toml
     5. /Users/max/Documents/GitHub/Mash agent  (Current directory)

   Select option [1-N], Enter to cancel, type another prompt:
   ```
   Folder entries are annotated `(folder)`. **The current directory is ALWAYS appended as the last option** with the `(Current directory)` suffix — selecting it routes into the action menu for the cwd itself (rename/move/copy/remove/chmod/add etc. all valid).
3. When listing a subdirectory the header uses the relative form:
   ```
   Mash listing ./test:

     1. /Users/max/Documents/GitHub/Mash agent/Claude_testing/test/app.py
     2. /Users/max/Documents/GitHub/Mash agent/Claude_testing/test/test.md
     3. /Users/max/Documents/GitHub/Mash agent/Claude_testing/test  (Current directory)

   Select option [1-N], Enter to cancel, type another prompt:
   ```
4. **Typed prompt → fuzzy match against the directory tree** (not a re-run of `mash`). Resolve the typed term against the current listing scope:
   - **Match is a folder** (1 hit) → switch the listing scope to that folder and re-render.
   - **Match is a folder, multiple hits** → render a folder-disambiguation menu (universal template); selecting one switches the listing scope.
   - **Match is a file** (1 hit) → narrow the current listing to that file and re-render the menu so the user can confirm and pick an action.
   - **Match is a file, multiple hits** → render a file-disambiguation menu; selecting one narrows the listing.
   - **No match** → repeat the listing menu with a `Mash could not find '<term>' in <scope>.` notice above the header.
   In every case the current directory remains the last option of the resulting menu.
5. Selecting `[1-N]` opens a **second** disambiguation menu listing every action mash can perform on the chosen item. The set is filtered by type (folder vs file) but mirrors the available templates:
   ```
   Selected: /Users/max/Documents/GitHub/Mash agent/mash  (folder)

     1. go into (cd)
     2. add (create file/folder inside)
     3. rename
     4. move
     5. copy
     6. remove
     7. list contents
     8. chmod

   Select option [1-M], Enter to cancel, type another prompt:
   ```
   For files, the action set is: `open`, `cat`, `rename`, `move`, `copy`, `remove`, `chmod`.
6. Selecting an action routes into that action's normal flow with the selected path pre-filled as the resolved source. From there mash follows the standard prompts for that action — destination prompts for move/copy (including the "no destination given" current-directory fallback), rename target prompt with extension reconciliation, delete safety prompt, run confirmation, etc.
7. **`add` on a folder** routes into the create flow with the chosen folder pre-filled as the destination. If the user enters a name with no extension, mash MUST run the extension picker before constructing the `touch` command — applies whether the user picks "create file" from the action menu or types a name directly.

**Command:** `ls -la <path>` for the initial listing; downstream commands depend on the chosen action.

---

## Open

**Trigger words:** `open`.

**Example:** `mash open report.pdf`

**Flow:**
1. Fuzzy-resolves source from args.
2. **Found** (single or multi-match) → universal numbered menu for source (same as move/copy).
3. After selection, mash asks an extra confirmation matching the delete layout:
   ```
   Are you sure you want to open:

      /Users/max/Documents/GitHub/Mash agent/report.pdf

   [y/N] :
   ```
   `N` / Enter cancels. `y` runs the command.
4. **Not found** → menu:
   ```
   Mash did not find a matching file, choose how to proceed:

     1. search for file
     2. cancel

   Select option [1-2], Enter to cancel, type another prompt:
   ```
   - `1` → mash re-scans the directory tree for the term. If a match is found, returns to step 2/3. If still nothing, the menu repeats.
   - `2` / Enter → cancel.

**Command:** `open <path>`

---

## Cat

**Trigger words:** `cat`, `show contents of`, `print`.

**Flow:** identical to **Open** — confirmation prompt with absolute path, same not-found search menu, same `[1-2]` footer.

```
Are you sure you want to cat:

   /Users/max/Documents/GitHub/Mash agent/report.md

[y/N] :
```

**Command:** `cat <path>`

---

## Chmod

`chmod` uses the universal numbered source menu and an inline permissions argument from the user. No destination prompts.

**Command:** `chmod <perm> <path>`

---

## Source resolution (all non-create actions)

1. Each non-stop-word arg is fuzzy-matched against the directory tree (`find . -maxdepth 4`, hidden files excluded), case-insensitive, `difflib` cutoff 0.6.
2. Results deduped, sorted by depth (shallowest first).
3. **0 candidates:**
   ```
   Mash did not find a matching file, choose how to proceed:

   Type a filename to search, Enter to cancel:
   ```
4. **1 candidate:** numbered menu with a single option, shown as an absolute path:
   ```
   Mash found a file:

     1. /Users/max/Documents/GitHub/Mash agent/report.pdf

   Select option [1], N to cancel, type another name:
   ```
5. **N candidates:** same template, `[1-N]`.

---

## Destination resolution (mv/cp)

1. Fuzzy-matches dest token against directories only.
2. Output uses the universal template. `<cwd>` (the actual current-directory name, not `./`) is shown as a selectable option for better readability.
3. **0/1 candidate:** menu with `create ./<token>` / `select <cwd>` / type another name.
4. **N candidates:** numbered menu including `<cwd>` as one of the options.

---

## Flag behavior

Both flags are development-only testing aids — not user-facing features.

| Flag | Effect |
|---|---|
| `--yes` / `-y` | Auto-selects first candidate in every disambiguation menu, skips all run confirmations and the delete safety prompt, executes command. |
| `--dry-run` | Same auto-selection as `--yes`, prints the command with `[dry-run]` and does **not** execute. Short-circuits browse mode (no interactive menu). |

---

## Command sanitisation

After the LLM responds, mash runs a deterministic post-processing pass before showing the command to the user:
- Replaces intent labels (`move_file`, etc.) with real verbs if the LLM echoed them.
- Strips leading `mkdir … &&` segments unless explicitly needed for create-in-new-dir.
- Downgrades `rm -rf` → `rm` and `cp -r` → `cp` when source type is `file` or `unknown`.
- Re-applies resolved source/destination/target name to the command, overriding any LLM drift.
