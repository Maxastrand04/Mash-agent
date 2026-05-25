import sys
from mash.intent import parse_intent
from mash.helpers.console import Console
from mash.helpers.llm import LLMClient, LLMError
from mash.helpers.selection import Disambig
from mash.helpers.files import get_directory_context
from mash.flows import move_copy_flow, rename_flow, delete_flow, create_flow, list_flow, open_cat_flow


def run() -> None:
    """CLI entry point: parse argv, extract flags, dispatch to run_with_args.

    Returns:
        None.

    Raises:
        SystemExit: When called with no positional args; prints usage
            and exits with status 1.
    """
    args = sys.argv[1:]
    yes = "--yes" in args or "-y" in args
    dry_run = "--dry-run" in args
    args = [a for a in args if a not in ("--yes", "-y", "--dry-run")]

    if not args:
        print("Usage: mash [--yes|-y] [--dry-run] <what you want to do>")
        sys.exit(1)

    run_with_args(args, yes, dry_run)


def run_with_args(args: list[str], yes: bool, dry_run: bool) -> None:
    """Construct collaborators and dispatch to the verb-specific flow.

    Builds Console, LLMClient, Disambig, and the directory context once
    per invocation. The trampoline allows list-mode pivots to re-enter
    the top-level dispatch with a fresh prompt while preserving flags.

    Args:
        args: Positional args after flag extraction.
        yes: Auto-confirm every prompt when True.
        dry_run: Print commands without executing when True.

    Returns:
        None.

    Raises:
        SystemExit: With status 1 when the LLM call fails.
    """
    intent = parse_intent(args)
    console = Console(yes, dry_run)
    llm = LLMClient()
    disambig = Disambig(console)
    context = get_directory_context()

    def _run_with_args_trampoline(new_args):
        run_with_args(new_args, yes, dry_run)

    try:
        if intent.verb == "cat" or intent.verb == "open":
            cmd = open_cat_flow(intent, console, llm, disambig, context, _run_with_args_trampoline)
            if cmd:
                console.confirm_and_run(cmd)
            return

        if intent.verb == "list":
            list_flow(intent.args, context, console, disambig, _run_with_args_trampoline)
            return

        if intent.verb == "rename":
            cmd = rename_flow(intent, console, llm, disambig, context)
            if cmd:
                console.confirm_and_run(cmd)
            return

        if intent.verb == "delete":
            result = delete_flow(intent, console, llm, disambig, context)
            if result:
                cmd, delete_path = result
                console.confirm_and_run(cmd, delete_path=delete_path)
            return

        if intent.verb == "create":
            cmd = create_flow(intent, console, llm, disambig, context)
            if cmd:
                console.confirm_and_run(cmd)
            return

        if intent.verb in ("move", "copy"):
            cmd = move_copy_flow(intent, console, llm, disambig, context)
            if cmd:
                console.confirm_and_run(cmd)
            return

        # Fallback for "other" verb — treat as move/copy flow
        cmd = move_copy_flow(intent, console, llm, disambig, context)
        if cmd:
            console.confirm_and_run(cmd)
    except LLMError:
        print("LLM not working, please try again")
        sys.exit(1)
