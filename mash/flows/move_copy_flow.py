import os

from mash.exceptions import UserCancelled, SourceNotFound, DestinationNotFound
from mash.helpers.files import PathResolver
from mash.helpers.commands import CommandSanitizer


class MoveCopyFlow:
    def __init__(self, console, llm_client, source_selector, destination_selector, directory_context):
        self.console = console
        self.llm_client = llm_client
        self.source_selector = source_selector
        self.destination_selector = destination_selector
        self.directory_context = directory_context

    def run(self, intent) -> str | None:
        try:
            return self._run(intent)
        except (UserCancelled, SourceNotFound, DestinationNotFound):
            print("Cancelled.")
            return None

    def _run(self, intent) -> str:
        seen: dict[str, None] = {}
        for word in intent.filtered_args:
            for path in PathResolver.resolve_paths(self.directory_context, word):
                seen[path] = None
        source_candidates = list(seen)

        resolved_source = self.source_selector.select(source_candidates, self.directory_context)

        source_type = "unknown"
        if resolved_source:
            if os.path.isfile(resolved_source):
                source_type = "file"
            elif os.path.isdir(resolved_source):
                source_type = "directory"

        action_verb = "copied" if intent.verb == "copy" else "moved"
        destination_candidates = (
            PathResolver.resolve_dirs(self.directory_context, intent.dest_token)
            if intent.dest_token is not None
            else []
        )
        destination, _should_create = self.destination_selector.select(
            destination_candidates,
            self.directory_context,
            destination_token=intent.dest_token,
            for_create=False,
            action_verb=action_verb,
        )

        command = self.llm_client.ask(
            prompt=intent.filtered_args,
            directory_context=self.directory_context,
            resolved_source=resolved_source,
            destination=destination,
            filename=None,
            source_type=source_type,
        )

        command = CommandSanitizer.normalize_template_verb(command)

        if "&&" in command:
            segments = [segment.strip() for segment in command.split("&&")]
            non_mkdir = [segment for segment in segments if not segment.lstrip().startswith("mkdir")]
            if non_mkdir:
                command = " && ".join(non_mkdir)

        command = CommandSanitizer.strip_recursive_flags(command, source_type)

        if resolved_source:
            command = CommandSanitizer.apply_source(command, resolved_source)
        if destination:
            command = CommandSanitizer.apply_destination(command, destination)

        return command
