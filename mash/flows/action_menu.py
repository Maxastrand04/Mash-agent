import os

from mash.helpers.files import Extensions
from mash.exceptions import UserCancelled, DestinationNotFound, InvalidExtension


class ActionMenu:
    def __init__(
        self,
        console,
        disambiguator,
        create_kind_picker,
        extension_picker,
        rename_extension_reconciler,
        destination_selector,
        run_with_args_fn,
    ):
        self.console = console
        self.disambiguator = disambiguator
        self.create_kind_picker = create_kind_picker
        self.extension_picker = extension_picker
        self.rename_extension_reconciler = rename_extension_reconciler
        self.destination_selector = destination_selector
        self.run_with_args_fn = run_with_args_fn

    def action_set(self, is_directory: bool) -> list[tuple[str, str]]:
        if is_directory:
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

    def show(self, selected_path: str, is_directory: bool, directory_context: str) -> None:
        abs_sel = self.console.abs_path(selected_path)
        actions = self.action_set(is_directory)
        suffix = "  (folder)" if is_directory else ""
        print()
        print(f"Selected: {abs_sel}{suffix}")
        m = len(actions)
        range_label = f"1-{m}"
        action_header = f"Choose action for {abs_sel}{suffix}:"
        prompt = self.console.render_menu(
            action_header,
            [label for label, _ in actions],
            f"Select option [{range_label}], Enter to cancel, type another prompt:",
        )
        ans = self.console.ask_input(prompt)
        if not ans:
            print("Cancelled.")
            return
        try:
            a_idx = int(ans) - 1
            if not (0 <= a_idx < m):
                raise ValueError
        except ValueError:
            new_args = ans.split()
            self.run_with_args_fn(new_args)
            return
        action = actions[a_idx][1]
        self.execute(action, selected_path, is_directory, directory_context)

    def execute(self, action: str, path: str, is_directory: bool, directory_context: str) -> None:
        abs_path = self.console.abs_path(path)
        if action == "go_into" or action == "list":
            self.run_with_args_fn(["list", "in", path])
            return
        if action == "add":
            try:
                kind = self.create_kind_picker.pick()
            except UserCancelled:
                print("Cancelled.")
                return
            if kind == "file":
                print(f"\nName for the new file (with extension):")
            else:
                print(f"\nName for the new folder:")
            name = self.console.ask_input("> ")
            if not name:
                print("Cancelled.")
                return
            if kind == "file":
                if "." not in name:
                    try:
                        extension = self.extension_picker.pick(directory_context)
                    except (UserCancelled, InvalidExtension):
                        print("Cancelled.")
                        return
                    name = f"{name}.{extension}"
                command = f"touch {path}/{name}"
            else:
                command = f"mkdir -p {path}/{name}"
            self.console.confirm_and_run(command)
            return
        if action == "rename":
            new_name = self.console.ask_input("\nNew name: ")
            if not new_name:
                print("Cancelled.")
                return
            final_after, prompt_kind = Extensions.reconcile_rename(path, new_name)
            if prompt_kind is not None:
                before_ext = os.path.splitext(path)[1]
                after_ext = os.path.splitext(new_name)[1]
                try:
                    final_after = self.rename_extension_reconciler.reconcile(
                        path, new_name, before_ext, after_ext, prompt_kind
                    )
                except UserCancelled:
                    print("Cancelled.")
                    return
            parent = os.path.dirname(path) or "."
            command = f"mv {path} {parent}/{final_after}"
            self.console.confirm_and_run(command)
            return
        if action in ("move", "copy"):
            verb_word = "moved" if action == "move" else "copied"
            try:
                destination, create_destination = self.destination_selector.select(
                    [],
                    directory_context,
                    destination_token=None,
                    for_create=False,
                    action_verb=verb_word,
                )
            except (UserCancelled, DestinationNotFound):
                print("Cancelled.")
                return
            verb = "mv" if action == "move" else ("cp -r" if is_directory else "cp")
            prefix = f"mkdir -p {destination} && " if create_destination else ""
            command = f"{prefix}{verb} {path} {destination.rstrip('/')}/"
            self.console.confirm_and_run(command)
            return
        if action == "remove":
            command = f"rm -rf {path}" if is_directory else f"rm {path}"
            self.console.confirm_and_run(command, delete_path=path)
            return
        if action == "open":
            if not self.console.confirm_action("open", abs_path):
                print("Cancelled.")
                return
            self.console.confirm_and_run(f"open {path}")
            return
        if action == "cat":
            if not self.console.confirm_action("cat", abs_path):
                print("Cancelled.")
                return
            self.console.confirm_and_run(f"cat {path}")
            return
        if action == "chmod":
            perm = self.console.ask_input("\nPermissions (e.g. 755): ")
            if not perm:
                print("Cancelled.")
                return
            self.console.confirm_and_run(f"chmod {perm} {path}")
            return
