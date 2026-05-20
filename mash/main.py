import sys
from mash.intent import parse_intent
from mash.helpers.console import Console
from mash.helpers.llm import LLMClient
from mash.helpers.files import get_directory_context
from mash.flows import move_copy_flow, rename_flow, delete_flow, create_flow, list_flow, open_cat_flow


def run() -> None:
    args = sys.argv[1:]
    yes = "--yes" in args or "-y" in args
    dry_run = "--dry-run" in args
    args = [a for a in args if a not in ("--yes", "-y", "--dry-run")]

    if not args:
        print("Usage: mash [--yes|-y] [--dry-run] <what you want to do>")
        sys.exit(1)

    run_with_args(args, yes, dry_run)


def run_with_args(args: list[str], yes: bool, dry_run: bool) -> None:
    intent = parse_intent(args)
    console = Console(yes, dry_run)
    llm = LLMClient()
    context = get_directory_context()

    def _run_with_args_trampoline(new_args):
        run_with_args(new_args, yes, dry_run)

    if intent.verb == "cat" or intent.verb == "open":
        cmd = open_cat_flow(intent, console, llm, context, _run_with_args_trampoline)
        if cmd:
            console.confirm_and_run(cmd)
        return

    if intent.verb == "list":
        list_flow(intent.args, context, console, _run_with_args_trampoline)
        return

    if intent.verb == "rename":
        cmd = rename_flow(intent, console, llm, context)
        if cmd:
            console.confirm_and_run(cmd)
        return

    if intent.verb == "delete":
        result = delete_flow(intent, console, llm, context)
        if result:
            cmd, delete_path = result
            console.confirm_and_run(cmd, delete_path=delete_path)
        return

    if intent.verb == "create":
        cmd = create_flow(intent, console, llm, context)
        if cmd:
            console.confirm_and_run(cmd)
        return

    if intent.verb in ("move", "copy"):
        cmd = move_copy_flow(intent, console, llm, context)
        if cmd:
            console.confirm_and_run(cmd)
        return

    # Fallback for "other" verb — treat as move/copy flow
    cmd = move_copy_flow(intent, console, llm, context)
    if cmd:
        console.confirm_and_run(cmd)
