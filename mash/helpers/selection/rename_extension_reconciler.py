import os

from mash.exceptions.user_cancelled import UserCancelled


class RenameExtensionReconciler:
    def __init__(self, console):
        self.console = console

    def reconcile(
        self,
        before_path: str,
        after_token: str,
        before_extension: str,
        after_extension: str,
        kind: str,
    ) -> str:
        stem_after = os.path.splitext(after_token)[0]
        if kind == "different_extension":
            keep_option = stem_after + before_extension
            if self.console.yes or self.console.dry_run:
                return keep_option
            print(
                f"\nThe new name changes the file extension from '{before_extension}' to '{after_extension}'."
                f" How do you want to proceed:\n"
            )
            print(f"  1. keep '{before_extension}' → {keep_option}")
            print(f"  2. use '{after_extension}' → {after_token}")
            print(f"  3. cancel")
            answer = self.console.ask_input(
                "\nSelect [1-3], Enter to keep original extension (1): "
            )
            if not answer:
                raise UserCancelled()
            if answer == "1":
                return keep_option
            if answer == "2":
                return after_token
            raise UserCancelled()
        else:
            keep_option = stem_after
            if self.console.yes or self.console.dry_run:
                return keep_option
            print(
                f"\nThe new name adds extension '{after_extension}' to a file that has none."
                f" How do you want to proceed:\n"
            )
            print(f"  1. keep no extension → {keep_option}")
            print(f"  2. add '{after_extension}' → {after_token}")
            print(f"  3. cancel")
            answer = self.console.ask_input(
                "\nSelect [1-3], Enter to keep no extension (1): "
            )
            if not answer:
                raise UserCancelled()
            if answer == "1":
                return keep_option
            if answer == "2":
                return after_token
            raise UserCancelled()
