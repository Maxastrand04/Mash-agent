from mash.helpers.files import resolve_paths


def select_source(
    candidates: list[str], context: str, console,
    query: str | None = None,
) -> str | None:
    if console.yes or console.dry_run:
        if not candidates:
            return None
        prefix = "[dry-run] " if console.dry_run else ""
        print(f"\n{prefix}Auto-selected: {candidates[0]}")
        return candidates[0]

    while True:
        if not candidates:
            q_label = f" for '{query}'" if query else ""
            prompt_str = console.render_menu(
                f"Mash did not find a matching file{q_label}, choose how to proceed:",
                [],
                "Type a filename to search, Enter to cancel:",
            )
            answer = console.ask_input(prompt_str)
            if not answer:
                return None
            query = answer
            candidates = resolve_paths(context, answer)
            continue

        n = len(candidates)
        q_label = f" for '{query}'" if query else ""
        if n == 1:
            header = f"Mash found a file{q_label}:"
        else:
            header = f"Mash found {n} files{q_label}:"
        range_label = "1" if n == 1 else f"1-{n}"
        footer = f"Select option [{range_label}], Enter to cancel, type name for other file/folder:"
        prompt_str = console.render_menu(header, [console.abs_path(p) for p in candidates], footer)
        answer = console.ask_input(prompt_str)
        if not answer:
            return None
        try:
            idx = int(answer) - 1
            if 0 <= idx < n:
                return candidates[idx]
        except ValueError:
            pass
        query = answer
        candidates = resolve_paths(context, answer)
