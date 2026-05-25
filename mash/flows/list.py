import os
import subprocess
import re
from mash.helpers.files import resolve_paths, resolve_dirs, collect_extensions, EXTENSION_MAP
from mash.helpers.files import reconcile_rename_extension
from mash.helpers.selection import Disambig
from mash.intent import _STOP_WORDS


def _scope_label(scope: str) -> str:
    """Format a directory path for display relative to cwd.

    Args:
        scope: Absolute or relative path to label.

    Returns:
        "." for cwd, "./relative" for paths inside cwd, or the absolute
        path when scope is outside cwd.

    Raises:
        None.
    """
    cwd = os.getcwd()
    abs_scope = os.path.abspath(scope)
    if abs_scope == cwd:
        return "."
    rel = os.path.relpath(abs_scope, start=cwd)
    if rel.startswith(".."):
        return abs_scope
    return f"./{rel}"


def _scoped_context(scope: str) -> str:
    """Build a directory-tree string rooted at scope for resolver lookups.

    Uses `find` with maxdepth 4 (matching the global context depth) and
    excludes dotfiles so the resolver sees the same surface a user would.

    Args:
        scope: Directory to scan.

    Returns:
        Newline-delimited list of paths under scope.

    Raises:
        None.
    """
    result = subprocess.run(
        ["find", scope, "-maxdepth", "4", "-not", "-path", "*/.*"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _list_entries(scope: str) -> list[tuple[str, bool]]:
    """List immediate children of scope, hiding dotfiles.

    Args:
        scope: Directory to list.

    Returns:
        Sorted list of (full_path, is_dir) tuples; empty on permission or
        OS errors so the caller can render a clean empty menu.

    Raises:
        None.
    """
    try:
        entries = sorted(os.listdir(scope))
    except OSError:
        return []
    entries = [e for e in entries if not e.startswith(".")]
    result = []
    for name in entries:
        full = os.path.join(scope, name)
        result.append((full, os.path.isdir(full)))
    return result


def _list_target_from_args(args: list[str], context: str) -> str:
    """Extract the directory the user wants listed from the raw args.

    Prefers tokens following preposition markers ("in", "inside", "of",
    "from") since users phrase listing as "list files in foo"; falls back
    to the first non-stopword that resolves to a directory.

    Args:
        args: The intent's raw argument tokens.
        context: Directory tree string used by resolve_dirs.

    Returns:
        The resolved directory path, or "." when nothing matches.

    Raises:
        None.
    """
    markers = {"in", "inside", "of", "from"}
    for i, w in enumerate(args):
        if w.lower() in markers and i + 1 < len(args):
            tok = args[i + 1]
            candidates = resolve_dirs(context, tok)
            if candidates:
                return candidates[0]
    for w in args:
        if w.lower() in _STOP_WORDS:
            continue
        candidates = resolve_dirs(context, w)
        if candidates:
            return candidates[0]
    return "."


def _action_set(is_dir: bool) -> list[tuple[str, str]]:
    """Return the action menu appropriate for the selected entry.

    Folder and file action sets differ: folders offer cd/list/add while
    files offer open/cat. Common actions (rename/move/copy/remove/chmod)
    appear in both.

    Args:
        is_dir: True when the selected entry is a directory.

    Returns:
        Ordered list of (display_label, action_key) pairs.

    Raises:
        None.
    """
    if is_dir:
        return [
            ("go into (cd)", "go_into"),
            ("add (create file/folder inside)", "add"),
            ("rename", "rename"),
            ("move", "move"),
            ("copy", "copy"),
            ("remove", "remove"),
            ("list contents", "list"),
            ("chmod", "chmod"),
        ]
    return [
        ("open", "open"),
        ("cat", "cat"),
        ("rename", "rename"),
        ("move", "move"),
        ("copy", "copy"),
        ("remove", "remove"),
        ("chmod", "chmod"),
    ]


def _ask_create_kind(console) -> str | None:
    """Disambiguate file-vs-folder when the "add" action is chosen.

    Mirrors the helper in create_flow so the list-mode "add" branch can
    behave identically without depending on the flow module.

    Args:
        console: Console helper for menus and input.

    Returns:
        "file" or "folder" on a valid selection; None on cancel or
        unrecognized input. Defaults to "file" in yes/dry_run mode.

    Raises:
        None.
    """
    if console.yes or console.dry_run:
        return "file"
    prompt_str = console.render_menu(
        "Mash is not sure what you want to create, choose:",
        ["create file", "create folder"],
        "Select option [1-2], Enter to cancel, type another prompt:",
    )
    answer = console.ask_input(prompt_str)
    if not answer:
        return None
    if answer == "1":
        return "file"
    if answer == "2":
        return "folder"
    return None


def _pick_extension_auto(context: str, console) -> str | None:
    """Non-interactive wrapper around _pick_extension_interactive.

    Picks the directory's most common existing extension (or "txt") in
    yes/dry_run mode so the flow can complete unattended.

    Args:
        context: Directory tree string used to harvest extensions.
        console: Console helper; consulted for yes/dry_run flags.

    Returns:
        The chosen extension without a leading dot, or None on cancel.

    Raises:
        None.
    """
    if console.yes or console.dry_run:
        exts = collect_extensions(context)
        return exts[0] if exts else "txt"
    return _pick_extension_interactive(context, console)


def _pick_extension_interactive(context: str, console) -> str | None:
    """Prompt for a file extension, biased toward existing siblings.

    Args:
        context: Directory tree string used to harvest extensions.
        console: Console helper for input.

    Returns:
        The chosen extension without a leading dot, or None on cancel.

    Raises:
        None.
    """
    dir_exts = collect_extensions(context)
    valid_set = set(dir_exts) | {v.lstrip(".") for v in EXTENSION_MAP.values()}

    while True:
        if dir_exts:
            print("\nWhat file extension?\n")
            for i, ext in enumerate(dir_exts, 1):
                print(f"  {i}. .{ext}")
            answer = console.ask_input(
                f"\nSelect extension [1-{len(dir_exts)}], type one manually (with or without dot), or Enter to cancel: "
            )
        else:
            answer = console.ask_input(
                "\nType a file extension (with or without dot), or Enter to cancel: "
            )

        if not answer:
            return None

        if dir_exts:
            try:
                idx = int(answer) - 1
                if 0 <= idx < len(dir_exts):
                    return dir_exts[idx]
            except ValueError:
                pass

        norm = answer.lstrip(".").lower()
        if not re.match(r'^[a-z0-9]{1,10}$', norm):
            print(f"Unknown extension '{norm}', try again.")
            continue
        if norm not in valid_set:
            print(f"Unknown extension '{norm}', try again.")
            continue
        return norm


def _apply_rename_reconciliation(before_path: str, after_token: str, console) -> str | None:
    """Resolve extension conflicts when renaming an entry inside list mode.

    Asks the user whether to keep the original extension, accept the new
    one, or cancel — only fires when the reconciler reports a mismatch.

    Args:
        before_path: Existing filesystem path being renamed.
        after_token: User-supplied new name (may or may not have an ext).
        console: Console helper for prompts.

    Returns:
        The final filename to use, or None if the user cancels.

    Raises:
        None.
    """
    final_after, prompt_kind = reconcile_rename_extension(before_path, after_token)
    if prompt_kind is None:
        return final_after
    if console.yes or console.dry_run:
        return final_after
    before_ext = os.path.splitext(before_path)[1]
    after_ext = os.path.splitext(after_token)[1]
    stem_after = os.path.splitext(after_token)[0]
    if prompt_kind == "different_extension":
        keep_option = stem_after + before_ext
        print(
            f"\nThe new name changes the file extension from '{before_ext}' to '{after_ext}'."
            f" How do you want to proceed:\n"
        )
        print(f"  1. keep '{before_ext}' → {keep_option}")
        print(f"  2. use '{after_ext}' → {after_token}")
        print(f"  3. cancel")
        answer = console.ask_input(
            "\nSelect [1-3], Enter to keep original extension (1): "
        )
        if not answer or answer == "1":
            return keep_option
        if answer == "2":
            return after_token
        return None
    else:
        keep_option = stem_after
        print(
            f"\nThe new name adds extension '{after_ext}' to a file that has none."
            f" How do you want to proceed:\n"
        )
        print(f"  1. keep no extension → {keep_option}")
        print(f"  2. add '{after_ext}' → {after_token}")
        print(f"  3. cancel")
        answer = console.ask_input(
            "\nSelect [1-3], Enter to keep no extension (1): "
        )
        if not answer or answer == "1":
            return keep_option
        if answer == "2":
            return after_token
        return None


def _show_action_menu(sel_path, is_dir, context, console, disambig, run_with_args_fn) -> None:
    """Render the per-entry action menu and dispatch the chosen action.

    Non-numeric input is treated as a fresh prompt and re-enters the CLI
    via run_with_args_fn so the user can pivot from a listing to any
    other intent without restarting.

    Args:
        sel_path: Path of the selected entry.
        is_dir: True when the selection is a directory.
        context: Directory tree string for downstream resolvers.
        console: Console helper for prompts.
        disambig: Disambiguation strategy passed to nested flows.
        run_with_args_fn: Callback to re-enter main with new args.

    Returns:
        None.

    Raises:
        None.
    """
    abs_sel = console.abs_path(sel_path)
    actions = _action_set(is_dir)
    suffix = "  (folder)" if is_dir else ""
    print()
    print(f"Selected: {abs_sel}{suffix}")
    m = len(actions)
    range_label2 = f"1-{m}"
    action_header = f"Choose action for {abs_sel}{suffix}:"
    a_prompt = console.render_menu(
        action_header,
        [label for label, _ in actions],
        f"Select option [{range_label2}], Enter to cancel, type another prompt:",
    )
    ans = console.ask_input(a_prompt)
    if not ans:
        print("Cancelled.")
        return
    try:
        a_idx = int(ans) - 1
        if not (0 <= a_idx < m):
            raise ValueError
    except ValueError:
        new_args = ans.split()
        run_with_args_fn(new_args)
        return
    action = actions[a_idx][1]
    _execute_list_action(action, sel_path, is_dir, context, console, disambig, run_with_args_fn)


def _execute_list_action(action, path, is_dir, context, console, disambig, run_with_args_fn) -> None:
    """Dispatch a chosen list-mode action to its concrete shell command.

    Each branch constructs a final command string deterministically and
    routes through console.confirm_and_run, so the LLM is bypassed for
    these in-list shortcuts — they are predictable user choices, not
    free-form prompts.

    Args:
        action: Action key from _action_set (e.g. "rename", "move").
        path: Path of the selected entry.
        is_dir: True when the selection is a directory.
        context: Directory tree string for nested flows.
        console: Console helper for prompts and execution.
        disambig: Disambiguation strategy for destination selection.
        run_with_args_fn: Re-entry callback (unused here, kept for symmetry).

    Returns:
        None.

    Raises:
        None.
    """
    abs_path = console.abs_path(path)
    if action == "go_into" or action == "list":
        list_flow(["list", "in", path], context, console, disambig, run_with_args_fn)
        return
    if action == "add":
        kind = _ask_create_kind(console)
        if kind is None:
            print("Cancelled.")
            return
        if kind == "file":
            print(f"\nName for the new file (with extension):")
        else:
            print(f"\nName for the new folder:")
        name = console.ask_input("> ")
        if not name:
            print("Cancelled.")
            return
        if kind == "file":
            if "." not in name:
                ext = _pick_extension_auto(context, console)
                if ext is None:
                    print("Cancelled.")
                    return
                name = f"{name}.{ext}"
            cmd = f"touch {path}/{name}"
        else:
            cmd = f"mkdir -p {path}/{name}"
        console.confirm_and_run(cmd)
        return
    if action == "rename":
        new_name = console.ask_input("\nNew name: ")
        if not new_name:
            print("Cancelled.")
            return
        final_after = _apply_rename_reconciliation(path, new_name, console)
        if final_after is None:
            print("Cancelled.")
            return
        parent = os.path.dirname(path) or "."
        cmd = f"mv {path} {parent}/{final_after}"
        console.confirm_and_run(cmd)
        return
    if action in ("move", "copy"):
        from mash.helpers.selection import select_destination
        verb_word = "moved" if action == "move" else "copied"
        dest, create_destination = select_destination(
            [], context, console, disambig, dest_token=None, for_create=False,
            action_verb=verb_word,
        )
        if dest is None:
            print("Cancelled.")
            return
        verb = "mv" if action == "move" else ("cp -r" if is_dir else "cp")
        prefix = f"mkdir -p {dest} && " if create_destination else ""
        cmd = f"{prefix}{verb} {path} {dest.rstrip('/')}/"
        console.confirm_and_run(cmd)
        return
    if action == "remove":
        cmd = f"rm -rf {path}" if is_dir else f"rm {path}"
        console.confirm_and_run(cmd, delete_path=path)
        return
    if action == "open":
        if not console.confirm_action("open", abs_path):
            print("Cancelled.")
            return
        console.confirm_and_run(f"open {path}")
        return
    if action == "cat":
        if not console.confirm_action("cat", abs_path):
            print("Cancelled.")
            return
        console.confirm_and_run(f"cat {path}")
        return
    if action == "chmod":
        perm = console.ask_input("\nPermissions (e.g. 755): ")
        if not perm:
            print("Cancelled.")
            return
        console.confirm_and_run(f"chmod {perm} {path}")
        return


def list_flow(args, context, console, disambig, run_with_args_fn) -> None:
    """Orchestrate the interactive listing flow.

    Renders the current scope's children, lets the user numerically pick
    an entry, narrow with a search term, descend into a folder, or pivot
    to a fresh prompt. Loops until an action is chosen or cancelled. In
    dry_run mode collapses to a single `ls -la` preview.

    Args:
        args: Raw intent argument tokens.
        context: Global directory tree string (used for nested resolvers).
        console: Console helper for prompts and execution.
        disambig: Disambiguation strategy for ambiguous narrowing.
        run_with_args_fn: Callback for pivoting to a new top-level prompt.

    Returns:
        None.

    Raises:
        None.
    """
    scope = _list_target_from_args(args, context)
    if console.dry_run:
        console.confirm_and_run(f"ls -la {_scope_label(scope)}")
        return
    narrowed: list[tuple[str, bool]] | None = None
    notice: str | None = None

    while True:
        entries = narrowed if narrowed is not None else _list_entries(scope)
        cwd_entry = (scope, True)
        all_entries = entries + [cwd_entry]

        options = []
        for full, is_dir in entries:
            abs_full = console.abs_path(full)
            label = f"{abs_full}  (folder)" if is_dir else abs_full
            options.append(label)
        options.append(console.cwd_label() if os.path.abspath(scope) == os.getcwd() else f"{console.abs_path(scope)}  (Current directory)")

        n = len(options)
        range_label = "1" if n == 1 else f"1-{n}"
        footer = f"Select option [{range_label}], Enter to cancel, type another prompt:"
        header = f"Mash listing {_scope_label(scope)}:"
        if notice:
            header = notice + "\n" + header
            notice = None

        if console.yes or console.dry_run:
            prefix = "[dry-run] " if console.dry_run else ""
            print(console.render_menu(header, options, footer).rstrip())
            print(f"\n{prefix}Auto-selected: {options[0]}")
            print("Cancelled.")
            return

        prompt_str = console.render_menu(header, options, footer)
        answer = console.ask_input(prompt_str)
        if not answer:
            print("Cancelled.")
            return
        try:
            idx = int(answer) - 1
            if not (0 <= idx < n):
                raise ValueError
        except ValueError:
            scoped_ctx = _scoped_context(scope)
            dir_hits = resolve_dirs(scoped_ctx, answer)
            file_hits = [p for p in resolve_paths(scoped_ctx, answer) if p not in dir_hits]
            if not dir_hits and not file_hits:
                lc = answer.lower()
                for full, is_dir in _list_entries(scope):
                    name = os.path.basename(full).lower()
                    if lc in name:
                        if is_dir:
                            dir_hits.append(full)
                        else:
                            file_hits.append(full)
            if len(dir_hits) == 1:
                scope = dir_hits[0]
                narrowed = None
                continue
            if len(dir_hits) > 1:
                kind, value = disambig.pick_from_hits(dir_hits, term=answer, kind="folder")
                if kind == "cancelled":
                    print("Cancelled.")
                    return
                if kind == "typed":
                    scoped_ctx = _scoped_context(scope)
                    re_dirs = resolve_dirs(scoped_ctx, value)
                    re_files = [p for p in resolve_paths(scoped_ctx, value) if p not in re_dirs]
                    if len(re_dirs) == 1:
                        scope = re_dirs[0]
                        narrowed = None
                        continue
                    if len(re_files) == 1:
                        p = re_files[0]
                        narrowed = [(p, os.path.isdir(p))]
                        continue
                    notice = f"Mash could not find '{value}' in {_scope_label(scope)}."
                    narrowed = None
                    continue
                scope = value
                narrowed = None
                continue
            if len(file_hits) == 1:
                p = file_hits[0]
                narrowed = [(p, os.path.isdir(p))]
                continue
            if len(file_hits) > 1:
                kind, value = disambig.pick_from_hits(file_hits, term=answer, kind="file")
                if kind == "cancelled":
                    print("Cancelled.")
                    return
                if kind == "typed":
                    scoped_ctx = _scoped_context(scope)
                    re_dirs = resolve_dirs(scoped_ctx, value)
                    re_files = [p for p in resolve_paths(scoped_ctx, value) if p not in re_dirs]
                    if len(re_files) == 1:
                        p = re_files[0]
                        narrowed = [(p, os.path.isdir(p))]
                        continue
                    if len(re_dirs) == 1:
                        scope = re_dirs[0]
                        narrowed = None
                        continue
                    notice = f"Mash could not find '{value}' in {_scope_label(scope)}."
                    narrowed = None
                    continue
                narrowed = [(value, os.path.isdir(value))]
                continue
            notice = f"Mash could not find '{answer}' in {_scope_label(scope)}."
            narrowed = None
            continue

        sel_path, is_dir = all_entries[idx]
        _show_action_menu(sel_path, is_dir, context, console, disambig, run_with_args_fn)
        return
