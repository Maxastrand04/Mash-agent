from mash.exceptions.user_cancelled import UserCancelled


class CreateKindPicker:
    def __init__(self, console):
        self.console = console

    def pick(self) -> str:
        if self.console.yes or self.console.dry_run:
            return "file"
        prompt = self.console.render_menu(
            "Mash is not sure what you want to create, choose:",
            ["create file", "create folder"],
            "Select option [1-2], Enter to cancel, type another prompt:",
        )
        answer = self.console.ask_input(prompt)
        if answer == "1":
            return "file"
        if answer == "2":
            return "folder"
        raise UserCancelled()
