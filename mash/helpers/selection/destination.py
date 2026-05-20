from mash.helpers.files import resolve_dirs


def select_destination(
    candidates: list[str], context: str, console,
    dest_token: str | None = None, for_create: bool = False,
    action_verb: str = "moved",
) -> tuple[str | None, bool]:
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
            options = [console.cwd_label()]
            footer = "Select option [1], Enter to cancel, type destination:"
            prompt_str = console.render_menu(
                f"Where should this be {action_verb}? Choose a destination:",
                options,
                footer,
            )
            answer = console.ask_input(prompt_str)
            if not answer:
                return None, False
            if answer == "1":
                return ".", False
            if answer.lower() == "n":
                return None, False
            new_candidates = resolve_dirs(context, answer)
            if new_candidates:
                if "." not in new_candidates:
                    new_candidates = new_candidates + ["."]
                candidates = new_candidates
                dest_token = answer
                no_dest_given = False
            else:
                dest_token = answer
                no_dest_given = False
            continue

        if for_create:
            if not real:
                if dest_token is None:
                    options = [console.cwd_label()]
                    footer = "Select option [1], Enter to cancel, type name for other destination:"
                    prompt_str = console.render_menu(
                        "Where should the new file/folder be created?",
                        options,
                        footer,
                    )
                    answer = console.ask_input(prompt_str)
                    if not answer:
                        return None, False
                    if answer == "1":
                        return ".", False
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
                    continue
                else:
                    token = dest_token
                    options = [
                        f"select {console.cwd_label()}",
                        f"create {console.abs_path('.')}/{token}",
                    ]
                    footer = "Select option [1-2], Enter to cancel, type name for other destination:"
                    prompt_str = console.render_menu(
                        f"Mash did not find directory '{token}', choose how to proceed:",
                        options,
                        footer,
                    )
                    answer = console.ask_input(prompt_str)
                    if not answer:
                        return None, False
                    if answer.lower() == "n":
                        return None, False
                    if answer == "1":
                        return ".", False
                    if answer == "2":
                        return f"./{token}", True
                    new_candidates = resolve_dirs(context, answer)
                    if new_candidates:
                        if "." not in new_candidates:
                            new_candidates = new_candidates + ["."]
                        candidates = new_candidates
                        dest_token = answer
                    else:
                        dest_token = answer
                    continue
            else:
                display = [
                    console.cwd_label() if c == "." else console.abs_path(c)
                    for c in candidates
                ]
                nopts = len(candidates)
                header_thing = "a folder" if len(real) == 1 else f"{len(real)} folders"
                token_label = f" for '{dest_token}'" if dest_token else ""
                header = f"Mash found {header_thing}{token_label}:"
                range_label = "1" if nopts == 1 else f"1-{nopts}"
                footer = f"Select option [{range_label}], Enter to cancel, type name for other destination:"
                prompt_str = console.render_menu(header, display, footer)
                answer = console.ask_input(prompt_str)
                if not answer:
                    return None, False
                if answer.lower() == "n":
                    return None, False
                try:
                    idx = int(answer) - 1
                    if 0 <= idx < nopts:
                        return candidates[idx], False
                except ValueError:
                    pass
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
                options = [
                    f"create {console.abs_path('.')}/{token}",
                    f"select {console.cwd_label()}",
                ]
                footer = "Select option [1-2], Enter to cancel, type name for other destination:"
                prompt_str = console.render_menu(
                    f"Mash did not find directory '{token}', choose how to proceed:",
                    options,
                    footer,
                )
                answer = console.ask_input(prompt_str)
                if not answer:
                    return None, False
                if answer.lower() == "n":
                    return None, False
                if answer == "1":
                    return f"./{token}", True
                if answer == "2":
                    return ".", False
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
                nopts = len(candidates)
                header_thing = "a folder" if len(real) == 1 else f"{len(real)} folders"
                token_label = f" for '{dest_token}'" if dest_token else ""
                header = f"Mash found {header_thing}{token_label}:"
                range_label = "1" if nopts == 1 else f"1-{nopts}"
                footer = f"Select option [{range_label}], Enter to cancel, type name for other destination:"
                prompt_str = console.render_menu(header, display, footer)
                answer = console.ask_input(prompt_str)
                if not answer:
                    return None, False
                if answer.lower() == "n":
                    return None, False
                try:
                    idx = int(answer) - 1
                    if 0 <= idx < nopts:
                        return candidates[idx], False
                except ValueError:
                    pass
                new_candidates = resolve_dirs(context, answer)
                if new_candidates:
                    if "." not in new_candidates:
                        new_candidates = new_candidates + ["."]
                    candidates = new_candidates
                else:
                    dest_token = answer
                    candidates = ["."]
                continue
