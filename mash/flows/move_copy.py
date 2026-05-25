import os
from mash.helpers.files import resolve_paths, resolve_dirs
from mash.helpers.selection import select_source, select_destination
from mash.helpers.commands import normalize_template_verb, apply_source, apply_destination, strip_recursive_flags
from mash.intent import _STOP_WORDS


def move_copy_flow(intent, console, llm, disambig, context) -> str | None:
    """Orchestrate the move and copy intents.

    Same shape for both verbs — the distinction is whether the LLM
    prompt and downstream sanitizers see "moved" or "copied" as the
    action verb. Strips spurious mkdir segments and recursive flags so
    files don't accidentally take `-r`.

    Args:
        intent: Parsed Intent describing the user request.
        console: Console helper for prompts and I/O.
        llm: LLMClient used to translate the prompt to a shell command.
        disambig: Disambiguation strategy passed through to selection.
        context: Directory tree string supplied to the LLM and resolvers.

    Returns:
        The final shell command, or None if the user cancels or the LLM
        returns nothing.

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

    source_type = "unknown"
    if resolved:
        if os.path.isfile(resolved):
            source_type = "file"
        elif os.path.isdir(resolved):
            source_type = "directory"

    is_copy = intent.verb == "copy"
    action_verb = "copied" if is_copy else "moved"
    dest_candidates = resolve_dirs(context, intent.dest_token) if intent.dest_token is not None else []
    destination, create_destination = select_destination(
        dest_candidates, context, console, disambig, intent.dest_token,
        for_create=False, action_verb=action_verb,
    )
    if destination is None:
        print("Cancelled.")
        return None

    prompt = " ".join(intent.args)
    cmd = llm.ask(prompt, context, resolved, destination, None, source_type=source_type)
    if not cmd:
        return None

    cmd = normalize_template_verb(cmd)

    if "&&" in cmd:
        segments = [s.strip() for s in cmd.split("&&")]
        non_mkdir = [s for s in segments if not s.lstrip().startswith("mkdir")]
        if non_mkdir:
            cmd = " && ".join(non_mkdir)

    cmd = strip_recursive_flags(cmd, source_type)

    if resolved:
        cmd = apply_source(cmd, resolved)
    if destination:
        cmd = apply_destination(cmd, destination)

    delete_path = None
    return cmd
