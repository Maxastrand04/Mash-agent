import os
import subprocess


class Console:
    """Thin I/O facade for menus, confirmations, and command execution.

    Centralizes the yes/dry_run flags so flow modules don't sprinkle the
    same conditional everywhere — non-interactive callers route through
    the same methods and get appropriate auto-answers.
    """

    def __init__(self, yes: bool, dry_run: bool):
        """Initialize the console with non-interactive flags.

        Args:
            yes: When True, auto-confirms every prompt.
            dry_run: When True, prints commands instead of executing.

        Returns:
            None.

        Raises:
            None.
        """
        self.yes = yes
        self.dry_run = dry_run

    def render_menu(self, header: str, options: list[str], footer: str) -> str:
        """Format a numbered menu as a single string for ask_input.

        Args:
            header: Title text shown above the option list.
            options: Display labels in display order.
            footer: Trailing prompt shown after the options.

        Returns:
            Concatenated multi-line menu string with a trailing space.

        Raises:
            None.
        """
        lines = ["", header, ""]
        for i, opt in enumerate(options, 1):
            lines.append(f"  {i}. {opt}")
        lines.append("")
        lines.append(footer)
        return "\n".join(lines) + " "

    def ask_input(self, prompt: str) -> str:
        """Read a single line from stdin, stripped of whitespace.

        EOF is swallowed and returned as the empty string so piped
        invocations (e.g. `echo "" | mash`) terminate cleanly.

        Args:
            prompt: Text printed to stdout before reading input.

        Returns:
            The user's input with leading/trailing whitespace removed,
            or "" on EOF.

        Raises:
            None.
        """
        try:
            return input(prompt).strip()
        except EOFError:
            return ""

    def confirm_yes_no(self, prompt: str) -> bool:
        """Read a y/N answer; anything other than lowercase 'y' is no.

        Args:
            prompt: Text printed to stdout before reading the answer.

        Returns:
            True only when the user typed exactly "y" (case-insensitive).

        Raises:
            None.
        """
        try:
            answer = input(prompt).strip().lower()
        except EOFError:
            answer = ""
        return answer == "y"

    def print_info(self, msg: str) -> None:
        """Emit an informational line to stdout.

        Args:
            msg: Message to print.

        Returns:
            None.

        Raises:
            None.
        """
        print(msg)

    def abs_path(self, path: str) -> str:
        """Return the absolute form of a filesystem path.

        Args:
            path: Relative or absolute path.

        Returns:
            The absolute path.

        Raises:
            None.
        """
        return os.path.abspath(path)

    def cwd_label(self) -> str:
        """Render the current working directory as a menu label.

        Returns:
            The cwd's absolute path followed by "(Current directory)".

        Raises:
            None.
        """
        return f"{os.path.abspath('.')}  (Current directory)"

    def confirm_action(self, verb: str, abs_path: str) -> bool:
        """Show a verb+path confirmation prompt and read y/N.

        Surfaced separately from confirm_and_run so callers can short-
        circuit before constructing a command (e.g. open/cat that have
        no side effects to roll back).

        Args:
            verb: Action description shown to the user ("open", "delete", …).
            abs_path: Absolute path being acted on.

        Returns:
            True on explicit "y" or when yes/dry_run skips the prompt.

        Raises:
            None.
        """
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
        """Show the command, confirm, then execute (unless dry_run).

        When delete_path is provided, an extra explicit delete-confirmation
        runs first so destructive operations require two acks (one for
        the path, one for the command). In yes mode both are skipped.

        Args:
            cmd: Shell command to execute via /bin/sh.
            delete_path: When set, triggers an additional delete confirm
                prompt and short-circuits on rejection.

        Returns:
            None.

        Raises:
            None.
        """
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
