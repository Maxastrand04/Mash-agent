from mash.helpers.files import resolve_paths
from mash.helpers.selection import select_source
from mash.intent import _STOP_WORDS


def _open_cat_not_found_menu(verb, context, console, disambig, run_with_args_fn) -> str | None:
    """Recovery loop when the user's open/cat target can't be resolved.

    Asks for a corrected term via the disambig strategy and retries
    resolution until a candidate emerges or the user cancels.

    Args:
        verb: "open" or "cat" (kept for future telemetry; unused today).
        context: Directory tree string for resolver calls.
        console: Console helper; consulted for yes/dry_run early-exit.
        disambig: Disambiguation strategy for the not-found prompt.
        run_with_args_fn: Re-entry callback (kept for signature parity).

    Returns:
        A resolved path, or None on cancel / non-interactive mode.

    Raises:
        None.
    """
    while True:
        if console.yes or console.dry_run:
            return None
        kind, value = disambig.pick_not_found(term=None)
        if kind == "cancelled":
            return None
        term = value
        candidates = resolve_paths(context, term)
        if candidates:
            resolved = select_source(candidates, context, console, disambig, query=term)
            if resolved is None:
                return None
            return resolved
        continue


def open_cat_flow(intent, console, llm, disambig, context, run_with_args_fn) -> str | None:
    """Orchestrate the open and cat intents.

    Builds the shell command deterministically (`open <path>` or
    `cat <path>`) without an LLM call — these verbs have no semantic
    ambiguity once the path is resolved. Strips the "show contents of"
    prefix so users can phrase cat naturally.

    Args:
        intent: Parsed Intent describing the user request.
        console: Console helper for prompts and confirmation.
        llm: LLMClient (accepted for signature parity; not invoked).
        disambig: Disambiguation strategy for source selection.
        context: Directory tree string for resolver calls.
        run_with_args_fn: Re-entry callback for the not-found loop.

    Returns:
        A shell command string, or None on cancel.

    Raises:
        None.
    """
    verb = "cat" if intent.verb == "cat" else "open"
    args = intent.args

    rest = args[1:]
    if args[0].lower() == "show" and len(args) >= 3 and args[1].lower() == "contents" and args[2].lower() == "of":
        rest = args[3:]
    seen: dict[str, None] = {}
    for word in rest:
        if word.lower() in _STOP_WORDS:
            continue
        for p in resolve_paths(context, word):
            seen[p] = None
    candidates = list(seen)
    first_query = next((w for w in rest if w.lower() not in _STOP_WORDS), None)
    if not candidates:
        resolved = _open_cat_not_found_menu(verb, context, console, disambig, run_with_args_fn)
    else:
        resolved = select_source(candidates, context, console, disambig, query=first_query)
    if resolved is None:
        print("Cancelled.")
        return None
    if not console.confirm_action(verb, console.abs_path(resolved)):
        print("Cancelled.")
        return None
    cmd = f"{verb} {resolved}"
    return cmd
