import sys
from mash.intent import Intent
from mash.helpers.console import Console
from mash.helpers.llm_client import LLMClient
from mash.helpers.selection import (
    Disambiguator,
    SourceSelector,
    DestinationSelector,
    CreateKindPicker,
    ExtensionPicker,
    RenameExtensionReconciler,
)
from mash.helpers.files import DirectoryContext
from mash.exceptions import LLMUnavailable, MashError
from mash.flows import (
    MoveCopyFlow,
    RenameFlow,
    DeleteFlow,
    CreateFlow,
    ListFlow,
    OpenCatFlow,
    BrowseMode,
    ActionMenu,
    ListScope,
)


class MashCLI:
    @classmethod
    def main(cls) -> None:
        cls().run()

    def __init__(self):
        self._yes = False
        self._dry_run = False

    def run(self) -> None:
        arguments = sys.argv[1:]
        self._yes = "--yes" in arguments or "-y" in arguments
        self._dry_run = "--dry-run" in arguments
        arguments = [a for a in arguments if a not in ("--yes", "-y", "--dry-run")]

        if not arguments:
            print("Usage: mash [--yes|-y] [--dry-run] <what you want to do>")
            sys.exit(1)

        self._run_with_args(arguments)

    def _run_with_args(self, arguments: list[str]) -> None:
        intent = Intent.parse(arguments)
        console = Console(self._yes, self._dry_run)
        llm_client = LLMClient()
        disambiguator = Disambiguator(console)
        directory_context = DirectoryContext.get()
        source_selector = SourceSelector(console, disambiguator)
        destination_selector = DestinationSelector(console, disambiguator)
        create_kind_picker = CreateKindPicker(console)
        extension_picker = ExtensionPicker(console)
        rename_extension_reconciler = RenameExtensionReconciler(console)

        try:
            if intent.verb in ("cat", "open"):
                flow = OpenCatFlow(
                    console,
                    llm_client,
                    source_selector,
                    disambiguator,
                    self._run_with_args,
                    directory_context,
                )
                command = flow.run(intent)
                if command:
                    console.confirm_and_run(command)
                return

            if intent.verb == "list":
                list_scope = ListScope()
                action_menu = ActionMenu(
                    console,
                    disambiguator,
                    create_kind_picker,
                    extension_picker,
                    rename_extension_reconciler,
                    destination_selector,
                    self._run_with_args,
                )
                browse_mode = BrowseMode(console, disambiguator, list_scope, action_menu)
                flow = ListFlow(
                    console,
                    disambiguator,
                    browse_mode,
                    action_menu,
                    list_scope,
                    self._run_with_args,
                    directory_context,
                )
                flow.run(intent)
                return

            if intent.verb == "rename":
                flow = RenameFlow(
                    console,
                    llm_client,
                    source_selector,
                    rename_extension_reconciler,
                    directory_context,
                )
                command = flow.run(intent)
                if command:
                    console.confirm_and_run(command)
                return

            if intent.verb == "delete":
                flow = DeleteFlow(console, llm_client, source_selector, directory_context)
                result = flow.run(intent)
                if result:
                    command, delete_path = result
                    console.confirm_and_run(command, delete_path=delete_path)
                return

            if intent.verb == "create":
                flow = CreateFlow(
                    console,
                    llm_client,
                    destination_selector,
                    create_kind_picker,
                    extension_picker,
                    directory_context,
                )
                command = flow.run(intent)
                if command:
                    console.confirm_and_run(command)
                return

            flow = MoveCopyFlow(
                console, llm_client, source_selector, destination_selector, directory_context
            )
            command = flow.run(intent)
            if command:
                console.confirm_and_run(command)

        except LLMUnavailable:
            print("LLM not working, please try again")
            sys.exit(1)
        except MashError as error:
            print(f"mash: {error}")
            sys.exit(1)
