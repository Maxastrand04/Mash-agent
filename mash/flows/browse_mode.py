import os

from mash.helpers.files import PathResolver


class BrowseMode:
    def __init__(self, console, disambiguator, list_scope, action_menu):
        self.console = console
        self.disambiguator = disambiguator
        self.list_scope = list_scope
        self.action_menu = action_menu

    def run(self, scope: str, directory_context: str, run_with_args_fn) -> None:
        narrowed: list[tuple[str, bool]] | None = None
        notice: str | None = None

        while True:
            entries = narrowed if narrowed is not None else self.list_scope.list_entries(scope)
            cwd_entry = (scope, True)
            all_entries = entries + [cwd_entry]

            options = []
            for full, is_dir in entries:
                abs_full = self.console.abs_path(full)
                label = f"{abs_full}  (folder)" if is_dir else abs_full
                options.append(label)
            options.append(
                self.console.cwd_label()
                if os.path.abspath(scope) == os.getcwd()
                else f"{self.console.abs_path(scope)}  (Current directory)"
            )

            n = len(options)
            range_label = "1" if n == 1 else f"1-{n}"
            footer = f"Select option [{range_label}], Enter to cancel, type another prompt:"
            header = f"Mash listing {self.list_scope.scope_label(scope)}:"
            if notice:
                header = notice + "\n" + header
                notice = None

            if self.console.yes or self.console.dry_run:
                prefix = "[dry-run] " if self.console.dry_run else ""
                print(self.console.render_menu(header, options, footer).rstrip())
                print(f"\n{prefix}Auto-selected: {options[0]}")
                print("Cancelled.")
                return

            prompt_str = self.console.render_menu(header, options, footer)
            answer = self.console.ask_input(prompt_str)
            if not answer:
                print("Cancelled.")
                return
            try:
                idx = int(answer) - 1
                if not (0 <= idx < n):
                    raise ValueError
            except ValueError:
                scoped_ctx = self.list_scope.scoped_context(scope)
                dir_hits = PathResolver.resolve_dirs(scoped_ctx, answer)
                file_hits = [
                    p for p in PathResolver.resolve_paths(scoped_ctx, answer)
                    if p not in dir_hits
                ]
                if not dir_hits and not file_hits:
                    lc = answer.lower()
                    for full, is_dir in self.list_scope.list_entries(scope):
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
                    selection = self.disambiguator.pick_from_hits(dir_hits, term=answer, kind="folder")
                    if selection.kind == "cancelled":
                        print("Cancelled.")
                        return
                    if selection.kind == "typed":
                        scoped_ctx = self.list_scope.scoped_context(scope)
                        re_dirs = PathResolver.resolve_dirs(scoped_ctx, selection.value)
                        re_files = [
                            p for p in PathResolver.resolve_paths(scoped_ctx, selection.value)
                            if p not in re_dirs
                        ]
                        if len(re_dirs) == 1:
                            scope = re_dirs[0]
                            narrowed = None
                            continue
                        if len(re_files) == 1:
                            p = re_files[0]
                            narrowed = [(p, os.path.isdir(p))]
                            continue
                        notice = f"Mash could not find '{selection.value}' in {self.list_scope.scope_label(scope)}."
                        narrowed = None
                        continue
                    scope = selection.value
                    narrowed = None
                    continue
                if len(file_hits) == 1:
                    p = file_hits[0]
                    narrowed = [(p, os.path.isdir(p))]
                    continue
                if len(file_hits) > 1:
                    selection = self.disambiguator.pick_from_hits(file_hits, term=answer, kind="file")
                    if selection.kind == "cancelled":
                        print("Cancelled.")
                        return
                    if selection.kind == "typed":
                        scoped_ctx = self.list_scope.scoped_context(scope)
                        re_dirs = PathResolver.resolve_dirs(scoped_ctx, selection.value)
                        re_files = [
                            p for p in PathResolver.resolve_paths(scoped_ctx, selection.value)
                            if p not in re_dirs
                        ]
                        if len(re_files) == 1:
                            p = re_files[0]
                            narrowed = [(p, os.path.isdir(p))]
                            continue
                        if len(re_dirs) == 1:
                            scope = re_dirs[0]
                            narrowed = None
                            continue
                        notice = f"Mash could not find '{selection.value}' in {self.list_scope.scope_label(scope)}."
                        narrowed = None
                        continue
                    narrowed = [(selection.value, os.path.isdir(selection.value))]
                    continue
                notice = f"Mash could not find '{answer}' in {self.list_scope.scope_label(scope)}."
                narrowed = None
                continue

            sel_path, is_dir = all_entries[idx]
            self.action_menu.show(sel_path, is_dir, directory_context)
            return
