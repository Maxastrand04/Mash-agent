import os
from mash.helpers.files import resolve_paths, reconcile_rename_extension
from mash.helpers.selection import select_source
from mash.helpers.commands import normalize_template_verb, apply_rename
from mash.intent import _STOP_WORDS


def _confirm_extension_change(
    before_path: str, after_token: str, before_ext: str, after_ext: str, kind: str, console,
) -> str | None:
    """Prompt the user to reconcile an extension change during rename.

    Two reconciliation kinds are distinguished: "different_extension"
    (before and after both have extensions, but they differ) and the
    add-extension case (before had none, after introduces one). The
    user can keep the original, accept the new, or cancel.

    Args:
        before_path: Existing filesystem path being renamed.
        after_token: User-supplied new name.
        before_ext: Original extension including dot, or empty.
        after_ext: New extension including dot, or empty.
        kind: "different_extension" or the add-extension case.
        console: Console helper for prompts.

    Returns:
        The final filename to use, or None if the user cancels.

    Raises:
        None.
    """
    stem_after = os.path.splitext(after_token)[0]
    if kind == "different_extension":
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
        if answer == "3" or answer.lower() == "n":
            return None
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
        if answer == "3" or answer.lower() == "n":
            return None
        return None


def rename_flow(intent, console, llm, disambig, context) -> str | None:
    """Orchestrate the rename intent.

    Resolves the source, reconciles any extension change with the user,
    asks the LLM for a rename command, then forces the target name onto
    the command via apply_rename so the LLM's output cannot drift from
    the user's chosen filename.

    Args:
        intent: Parsed Intent describing the user request.
        console: Console helper for prompts and I/O.
        llm: LLMClient used to translate the prompt to a shell command.
        disambig: Disambiguation strategy passed through to selection.
        context: Directory tree string supplied to the LLM and resolvers.

    Returns:
        The final shell command, or None on cancel / empty LLM output.

    Raises:
        None.
    """
    seen: dict[str, None] = {}
    for word in intent.filtered_args:
        if word.lower() not in _STOP_WORDS:
            for p in resolve_paths(context, word):
                seen[p] = None
    source_candidates = list(seen)

    source_query = next(
        (w for w in intent.filtered_args if w.lower() not in _STOP_WORDS), None
    )
    resolved = select_source(source_candidates, context, console, disambig, query=source_query)
    if resolved is None and not (console.yes or console.dry_run):
        print("Cancelled.")
        return None

    rename_target = intent.rename_target
    destination = None

    if resolved and rename_target:
        final_after, prompt_kind = reconcile_rename_extension(resolved, rename_target)
        if prompt_kind is not None and not (console.yes or console.dry_run):
            before_ext = os.path.splitext(resolved)[1]
            after_ext = os.path.splitext(rename_target)[1]
            result = _confirm_extension_change(
                resolved, rename_target, before_ext, after_ext, prompt_kind, console
            )
            if result is None:
                print("Cancelled.")
                return None
            final_after = result
        rename_target = final_after

    prompt = " ".join(intent.args)
    cmd = llm.ask(prompt, context, resolved, destination, None, after=rename_target)
    if not cmd:
        return None

    cmd = normalize_template_verb(cmd)

    if "&&" in cmd:
        segments = [s.strip() for s in cmd.split("&&")]
        non_mkdir = [s for s in segments if not s.lstrip().startswith("mkdir")]
        if non_mkdir:
            cmd = " && ".join(non_mkdir)

    if resolved and rename_target:
        cmd = apply_rename(cmd, resolved, rename_target, intent.dest_token)

    return cmd
