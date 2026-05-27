import os
from mash.helpers.files.path_resolver import PathResolver
from mash.helpers.commands.command_sanitizer import CommandSanitizer
from mash.exceptions import UserCancelled, SourceNotFound, LLMUnavailable
from mash.intent import Intent


class DeleteFlow:
    def __init__(self, console, llm_client, source_selector, directory_context: str):
        self._console = console
        self._llm_client = llm_client
        self._source_selector = source_selector
        self._directory_context = directory_context

    def run(self, intent) -> tuple[str, str | None] | None:
        try:
            return self._run(intent)
        except (UserCancelled, SourceNotFound):
            print("Cancelled.")
            return None

    def _run(self, intent) -> tuple[str, str | None]:
        seen: dict[str, None] = {}
        for word in intent.filtered_args:
            if word.lower() not in Intent._STOP_WORDS:
                for p in PathResolver.resolve_paths(self._directory_context, word):
                    seen[p] = None
        source_candidates = list(seen)

        source_query = next(
            (w for w in intent.filtered_args if w.lower() not in Intent._STOP_WORDS), None
        )
        resolved = self._source_selector.select(
            source_candidates, self._directory_context, query=source_query
        )

        source_type = "unknown"
        if resolved:
            if os.path.isfile(resolved):
                source_type = "file"
            elif os.path.isdir(resolved):
                source_type = "directory"

        prompt = " ".join(intent.args)
        command = self._llm_client.ask(
            prompt=prompt,
            directory_context=self._directory_context,
            resolved_source=resolved,
            destination=None,
            filename=None,
            source_type=source_type,
        )
        if not command:
            raise LLMUnavailable("LLM returned empty response")

        command = CommandSanitizer.normalize_template_verb(command)

        if "&&" in command:
            segments = [s.strip() for s in command.split("&&")]
            non_mkdir = [s for s in segments if not s.lstrip().startswith("mkdir")]
            if non_mkdir:
                command = " && ".join(non_mkdir)

        command = CommandSanitizer.strip_recursive_flags(command, source_type)

        if resolved:
            command = CommandSanitizer.apply_source(command, resolved)

        delete_path = resolved if command.split()[:1] == ["rm"] and resolved else None
        return command, delete_path
