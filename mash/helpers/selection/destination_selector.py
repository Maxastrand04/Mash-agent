from mash.exceptions.destination_not_found import DestinationNotFound
from mash.helpers.files.path_resolver import PathResolver


class DestinationSelector:
    def __init__(self, console, disambiguator):
        self.console = console
        self.disambiguator = disambiguator

    def select(
        self,
        candidates: list[str],
        directory_context: str,
        destination_token: str | None = None,
        for_create: bool = False,
        action_verb: str = "moved",
    ) -> tuple[str, bool]:
        console = self.console
        disambiguator = self.disambiguator

        if "." not in candidates:
            candidates = candidates + ["."]

        if console.yes or console.dry_run:
            prefix = "[dry-run] " if console.dry_run else ""
            real = [c for c in candidates if c != "."]
            if for_create and destination_token is not None and not real:
                chosen = f"./{destination_token}"
                print(f"\n{prefix}Auto-selected destination: {chosen}")
                return chosen, True
            if not for_create and destination_token is None and not real:
                raise DestinationNotFound("<no destination>")
            chosen = candidates[0] if len(candidates) > 1 else "."
            print(f"\n{prefix}Auto-selected destination: {chosen}")
            return chosen, False

        no_destination_given = destination_token is None and not for_create

        while True:
            real = [c for c in candidates if c != "."]

            if no_destination_given and not real:
                header = f"Where should this be {action_verb}? Choose a destination:"
                actions = [(f"select {console.cwd_label()}", "select_cwd")]
                selection = disambiguator.pick_with_actions(
                    hits=[], actions=actions, header=header,
                )
                if selection.kind == "action" and selection.value == "select_cwd":
                    return ".", False
                answer = selection.value
                new_candidates = PathResolver.resolve_dirs(directory_context, answer)
                if new_candidates:
                    candidates = new_candidates + ["."]
                destination_token = answer
                no_destination_given = False
                continue

            if for_create:
                if not real:
                    if destination_token is None:
                        header = "Where should the new file/folder be created?"
                        actions = [(f"select {console.cwd_label()}", "select_cwd")]
                        selection = disambiguator.pick_with_actions(
                            hits=[], actions=actions, header=header,
                        )
                        if selection.kind == "action" and selection.value == "select_cwd":
                            return ".", False
                        answer = selection.value
                        new_candidates = PathResolver.resolve_dirs(directory_context, answer)
                        if new_candidates:
                            candidates = new_candidates + ["."]
                        destination_token = answer
                        continue
                    else:
                        token = destination_token
                        header = f"Mash did not find directory '{token}', choose how to proceed:"
                        actions = [
                            (f"select {console.cwd_label()}", "select_cwd"),
                            (f"create {console.abs_path('.')}/{token}", "create_here"),
                        ]
                        selection = disambiguator.pick_with_actions(
                            hits=[], actions=actions, header=header,
                        )
                        if selection.kind == "action":
                            if selection.value == "select_cwd":
                                return ".", False
                            if selection.value == "create_here":
                                return f"./{token}", True
                        answer = selection.value
                        new_candidates = PathResolver.resolve_dirs(directory_context, answer)
                        if new_candidates:
                            candidates = new_candidates + ["."]
                        destination_token = answer
                        continue
                else:
                    display = [
                        console.cwd_label() if c == "." else console.abs_path(c)
                        for c in candidates
                    ]
                    header_thing = "a folder" if len(real) == 1 else f"{len(real)} folders"
                    token_label = f" for '{destination_token}'" if destination_token else ""
                    header = f"Mash found {header_thing}{token_label}:"
                    selection = disambiguator.pick_with_actions(
                        hits=candidates, actions=[], header=header, display=display,
                    )
                    if selection.kind == "selected":
                        return selection.value, False
                    answer = selection.value
                    new_candidates = PathResolver.resolve_dirs(directory_context, answer)
                    if new_candidates:
                        candidates = new_candidates + ["."]
                        destination_token = answer
                    else:
                        destination_token = answer
                        candidates = ["."]
                    continue
            else:
                if not real:
                    token = destination_token or "unknown"
                    header = f"Mash did not find directory '{token}', choose how to proceed:"
                    actions = [
                        (f"create {console.abs_path('.')}/{token}", "create_here"),
                        (f"select {console.cwd_label()}", "select_cwd"),
                    ]
                    selection = disambiguator.pick_with_actions(
                        hits=[], actions=actions, header=header,
                    )
                    if selection.kind == "action":
                        if selection.value == "create_here":
                            return f"./{token}", True
                        if selection.value == "select_cwd":
                            return ".", False
                    answer = selection.value
                    new_candidates = PathResolver.resolve_dirs(directory_context, answer)
                    if new_candidates:
                        candidates = new_candidates + ["."]
                    else:
                        destination_token = answer
                    continue
                else:
                    display = [
                        console.cwd_label() if c == "." else console.abs_path(c)
                        for c in candidates
                    ]
                    header_thing = "a folder" if len(real) == 1 else f"{len(real)} folders"
                    token_label = f" for '{destination_token}'" if destination_token else ""
                    header = f"Mash found {header_thing}{token_label}:"
                    selection = disambiguator.pick_with_actions(
                        hits=candidates, actions=[], header=header, display=display,
                    )
                    if selection.kind == "selected":
                        return selection.value, False
                    answer = selection.value
                    new_candidates = PathResolver.resolve_dirs(directory_context, answer)
                    if new_candidates:
                        candidates = new_candidates + ["."]
                    else:
                        destination_token = answer
                        candidates = ["."]
                    continue
