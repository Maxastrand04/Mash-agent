from mash.helpers.files import resolve_paths
from mash.helpers.selection import select_source
from mash.intent import _STOP_WORDS


def _open_cat_not_found_menu(verb, context, console, run_with_args_fn) -> str | None:
    while True:
        if console.yes or console.dry_run:
            return None
        prompt_str = console.render_menu(
            "Mash did not find a matching file, choose how to proceed:",
            ["search for file", "cancel"],
            "Select option [1-2], Enter to cancel, type another prompt:",
        )
        answer = console.ask_input(prompt_str)
        if not answer or answer == "2":
            return None
        if answer == "1":
            term = console.ask_input("\nSearch term: ")
            if not term:
                return None
            candidates = resolve_paths(context, term)
            if candidates:
                resolved = select_source(candidates, context, console, query=term)
                if resolved is None:
                    return None
                return resolved
            continue
        run_with_args_fn(answer.split())
        return None


def open_cat_flow(intent, console, llm, context, run_with_args_fn) -> str | None:
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
        resolved = _open_cat_not_found_menu(verb, context, console, run_with_args_fn)
    else:
        resolved = select_source(candidates, context, console, query=first_query)
    if resolved is None:
        print("Cancelled.")
        return None
    if not console.confirm_action(verb, console.abs_path(resolved)):
        print("Cancelled.")
        return None
    cmd = f"{verb} {resolved}"
    return cmd
