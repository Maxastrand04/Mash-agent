import re

from mash.exceptions.invalid_extension import InvalidExtension
from mash.exceptions.user_cancelled import UserCancelled
from mash.helpers.files.extensions import Extensions


class ExtensionPicker:
    def __init__(self, console):
        self.console = console

    def pick(self, directory_context: str) -> str:
        directory_extensions = Extensions.collect(directory_context)

        if self.console.yes or self.console.dry_run:
            if directory_extensions:
                return directory_extensions[0]
            return "txt"

        valid_set = set(directory_extensions) | {
            value.lstrip(".") for value in Extensions.EXTENSION_MAP.values()
        }

        if directory_extensions:
            prompt = self.console.render_menu(
                "What file extension?",
                [f".{extension}" for extension in directory_extensions],
                f"Select extension [1-{len(directory_extensions)}], "
                "type one manually (with or without dot), or Enter to cancel:",
            )
        else:
            prompt = "\nType a file extension (with or without dot), or Enter to cancel: "

        answer = self.console.ask_input(prompt)

        if not answer:
            raise UserCancelled()

        if directory_extensions:
            try:
                index = int(answer)
            except ValueError:
                index = 0
            if 1 <= index <= len(directory_extensions):
                return directory_extensions[index - 1]

        normalized = answer.lstrip(".").lower()
        if not re.match(r"^[a-z0-9]{1,10}$", normalized) or normalized not in valid_set:
            raise InvalidExtension(normalized)

        return normalized
