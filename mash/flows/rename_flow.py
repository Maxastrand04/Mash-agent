import os

from mash.exceptions.user_cancelled import UserCancelled
from mash.exceptions.source_not_found import SourceNotFound
from mash.exceptions.llm_unavailable import LLMUnavailable
from mash.helpers.files.extensions import Extensions
from mash.helpers.files.path_resolver import PathResolver
from mash.helpers.commands.command_sanitizer import CommandSanitizer
from mash.intent import Intent


class RenameFlow:
    def __init__(self, console, llm_client, source_selector, rename_extension_reconciler, directory_context: str):
        self.console = console
        self.llm_client = llm_client
        self.source_selector = source_selector
        self.rename_extension_reconciler = rename_extension_reconciler
        self.directory_context = directory_context

    def run(self, intent) -> str | None:
        try:
            seen: dict[str, None] = {}
            for word in intent.filtered_args:
                if word.lower() not in Intent._STOP_WORDS:
                    for path in PathResolver.resolve_paths(self.directory_context, word):
                        seen[path] = None
            source_candidates = list(seen)

            resolved_source = self.source_selector.select(source_candidates, self.directory_context)

            rename_target = intent.rename_target
            final_name, kind = Extensions.reconcile_rename(resolved_source, rename_target)

            if kind is not None:
                before_extension = os.path.splitext(resolved_source)[1]
                after_extension = os.path.splitext(final_name)[1]
                final_name = self.rename_extension_reconciler.reconcile(
                    resolved_source, intent.rename_target, before_extension, after_extension, kind
                )

            command = self.llm_client.ask(
                prompt=intent.filtered_args,
                directory_context=self.directory_context,
                resolved_source=resolved_source,
                destination="",
                filename=None,
                after_path=final_name,
            )

            if not command:
                raise LLMUnavailable("LLM returned empty response")

            command = CommandSanitizer.normalize_template_verb(command)

            if "&&" in command:
                parts = [part.strip() for part in command.split("&&")]
                non_mkdir = [part for part in parts if not part.lstrip().startswith("mkdir")]
                if non_mkdir:
                    command = " && ".join(non_mkdir)

            command = CommandSanitizer.apply_rename(command, before_path=resolved_source, after_path=final_name)

            return command

        except (UserCancelled, SourceNotFound):
            print("Cancelled.")
            return None
