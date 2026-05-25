from mash.helpers.files import resolve_dirs


def select_destination(
    candidates: list[str], context: str, console, disambig,
    dest_token: str | None = None, for_create: bool = False,
    action_verb: str = "moved",
) -> tuple[str | None, bool]:
    """Resolve a destination directory with optional create-on-miss support.

    Three modes: create-mode (for_create=True) lets the user choose to
    mkdir a non-existent destination; move/copy mode also offers
    create-here but uses a different header; the no-destination-given
    branch lets the user pick the cwd. Returns a (path, create) tuple
    where create signals the caller to prepend `mkdir -p` to the command.

    Args:
        candidates: Pre-resolved candidate directories.
        context: Directory tree for additional resolver calls.
        console: Console helper for yes/dry_run and rendering.
        disambig: Disambiguation strategy for the picker UI.
        dest_token: The original user token (used in headers and for
            constructing a new path on create-here).
        for_create: True when this is a create flow.
        action_verb: Past-tense verb shown in the "Where should this be
            <verb>?" header for move/copy ("moved" or "copied").

    Returns:
        (destination, create_destination) where destination is None on
        cancel and create_destination is True only when the user chose
        to mkdir a new directory.

    Raises:
        None.
    """
    if "." not in candidates:
        candidates = candidates + ["."]

    if console.yes or console.dry_run:
        prefix = "[dry-run] " if console.dry_run else ""
        real = [c for c in candidates if c != "."]
        if for_create and dest_token is not None and not real:
            chosen = f"./{dest_token}"
            print(f"\n{prefix}Auto-selected destination: {chosen}")
            return chosen, True
        chosen = candidates[0] if len(candidates) > 1 else "."
        print(f"\n{prefix}Auto-selected destination: {chosen}")
        return chosen, False

    no_dest_given = dest_token is None and not for_create

    while True:
        real = [c for c in candidates if c != "."]

        if no_dest_given and not real:
            header = f"Where should this be {action_verb}? Choose a destination:"
            actions = [(f"select {console.cwd_label()}", "select_cwd")]
            kind, value = disambig.pick_with_actions(
                hits=[], actions=actions, header=header,
            )
            if kind == "cancelled":
                return None, False
            if kind == "action" and value == "select_cwd":
                return ".", False
            # typed
            answer = value
            if answer.lower() == "n":
                return None, False
            new_candidates = resolve_dirs(context, answer)
            if new_candidates:
                if "." not in new_candidates:
                    new_candidates = new_candidates + ["."]
                candidates = new_candidates
            dest_token = answer
            no_dest_given = False
            continue

        if for_create:
            if not real:
                if dest_token is None:
                    header = "Where should the new file/folder be created?"
                    actions = [(f"select {console.cwd_label()}", "select_cwd")]
                    kind, value = disambig.pick_with_actions(
                        hits=[], actions=actions, header=header,
                    )
                    if kind == "cancelled":
                        return None, False
                    if kind == "action" and value == "select_cwd":
                        return ".", False
                    answer = value
                    if answer.lower() == "n":
                        return None, False
                    new_candidates = resolve_dirs(context, answer)
                    if new_candidates:
                        if "." not in new_candidates:
                            new_candidates = new_candidates + ["."]
                        candidates = new_candidates
                    dest_token = answer
                    continue
                else:
                    token = dest_token
                    header = f"Mash did not find directory '{token}', choose how to proceed:"
                    actions = [
                        (f"select {console.cwd_label()}", "select_cwd"),
                        (f"create {console.abs_path('.')}/{token}", "create_here"),
                    ]
                    kind, value = disambig.pick_with_actions(
                        hits=[], actions=actions, header=header,
                    )
                    if kind == "cancelled":
                        return None, False
                    if kind == "action":
                        if value == "select_cwd":
                            return ".", False
                        if value == "create_here":
                            return f"./{token}", True
                    answer = value
                    if answer.lower() == "n":
                        return None, False
                    new_candidates = resolve_dirs(context, answer)
                    if new_candidates:
                        if "." not in new_candidates:
                            new_candidates = new_candidates + ["."]
                        candidates = new_candidates
                    dest_token = answer
                    continue
            else:
                display = [
                    console.cwd_label() if c == "." else console.abs_path(c)
                    for c in candidates
                ]
                header_thing = "a folder" if len(real) == 1 else f"{len(real)} folders"
                token_label = f" for '{dest_token}'" if dest_token else ""
                header = f"Mash found {header_thing}{token_label}:"
                kind, value = disambig.pick_with_actions(
                    hits=candidates, actions=[], header=header, display=display,
                )
                if kind == "cancelled":
                    return None, False
                if kind == "selected":
                    return value, False
                answer = value
                if answer.lower() == "n":
                    return None, False
                new_candidates = resolve_dirs(context, answer)
                if new_candidates:
                    if "." not in new_candidates:
                        new_candidates = new_candidates + ["."]
                    candidates = new_candidates
                    dest_token = answer
                else:
                    dest_token = answer
                    candidates = ["."]
                continue
        else:
            if not real:
                token = dest_token or "unknown"
                header = f"Mash did not find directory '{token}', choose how to proceed:"
                actions = [
                    (f"create {console.abs_path('.')}/{token}", "create_here"),
                    (f"select {console.cwd_label()}", "select_cwd"),
                ]
                kind, value = disambig.pick_with_actions(
                    hits=[], actions=actions, header=header,
                )
                if kind == "cancelled":
                    return None, False
                if kind == "action":
                    if value == "create_here":
                        return f"./{token}", True
                    if value == "select_cwd":
                        return ".", False
                answer = value
                if answer.lower() == "n":
                    return None, False
                new_candidates = resolve_dirs(context, answer)
                if new_candidates:
                    if "." not in new_candidates:
                        new_candidates = new_candidates + ["."]
                    candidates = new_candidates
                else:
                    dest_token = answer
                continue
            else:
                display = [
                    console.cwd_label() if c == "." else console.abs_path(c)
                    for c in candidates
                ]
                header_thing = "a folder" if len(real) == 1 else f"{len(real)} folders"
                token_label = f" for '{dest_token}'" if dest_token else ""
                header = f"Mash found {header_thing}{token_label}:"
                kind, value = disambig.pick_with_actions(
                    hits=candidates, actions=[], header=header, display=display,
                )
                if kind == "cancelled":
                    return None, False
                if kind == "selected":
                    return value, False
                answer = value
                if answer.lower() == "n":
                    return None, False
                new_candidates = resolve_dirs(context, answer)
                if new_candidates:
                    if "." not in new_candidates:
                        new_candidates = new_candidates + ["."]
                    candidates = new_candidates
                else:
                    dest_token = answer
                    candidates = ["."]
                continue
