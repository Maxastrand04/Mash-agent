import os
import subprocess


class Console:
    def __init__(self, yes: bool, dry_run: bool):
        self.yes = yes
        self.dry_run = dry_run

    def render_menu(self, header: str, options: list[str], footer: str) -> str:
        lines = ["", header, ""]
        for i, opt in enumerate(options, 1):
            lines.append(f"  {i}. {opt}")
        lines.append("")
        lines.append(footer)
        return "\n".join(lines) + " "

    def ask_input(self, prompt: str) -> str:
        try:
            return input(prompt).strip()
        except EOFError:
            return ""

    def confirm_yes_no(self, prompt: str) -> bool:
        try:
            answer = input(prompt).strip().lower()
        except EOFError:
            answer = ""
        return answer == "y"

    def print_info(self, msg: str) -> None:
        print(msg)

    def abs_path(self, path: str) -> str:
        return os.path.abspath(path)

    def cwd_label(self) -> str:
        return f"{os.path.abspath('.')}  (Current directory)"

    def confirm_action(self, verb: str, abs_path: str) -> bool:
        if self.yes or self.dry_run:
            return True
        print(f"\nAre you sure you want to {verb}:")
        print()
        print(f"   {abs_path}")
        print()
        try:
            answer = input("[y/N] : ").strip().lower()
        except EOFError:
            answer = ""
        return answer == "y"

    def confirm_and_run(
        self, cmd: str, delete_path: str | None = None,
    ) -> None:
        if delete_path and not self.confirm_action("delete", self.abs_path(delete_path)):
            print("Cancelled.")
            return
        print(f"\nRun: {cmd}")
        if self.dry_run:
            print("[dry-run] command not executed.")
            return
        if self.yes:
            subprocess.run(cmd, shell=True)
            return
        try:
            answer = input("[y/N] ").strip().lower()
        except EOFError:
            answer = ""
        if answer == "y":
            subprocess.run(cmd, shell=True)
        else:
            print("Cancelled.")
