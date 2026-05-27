from typing import Callable

from mash.exceptions import UserCancelled, SourceNotFound
from mash.helpers.files.path_resolver import PathResolver
from mash.intent import Intent


class OpenCatFlow:
    def __init__(
        self,
        console,
        llm_client,
        source_selector,
        disambiguator,
        run_with_args_fn: Callable[[list[str]], None],
        directory_context: str,
    ):
        self._console = console
        self._llm_client = llm_client
        self._source_selector = source_selector
        self._disambiguator = disambiguator
        self._run_with_args_fn = run_with_args_fn
        self._directory_context = directory_context
        self._path_resolver = PathResolver()

    def run(self, intent) -> str | None:
        try:
            return self._run_intent(intent)
        except UserCancelled:
            print("Cancelled.")
            return None
        except SourceNotFound:
            print("Cancelled.")
            return None

    def _run_intent(self, intent) -> str:
        verb = "cat" if intent.verb == "cat" else "open"
        args = intent.args

        rest = args[1:]
        if (
            args[0].lower() == "show"
            and len(args) >= 3
            and args[1].lower() == "contents"
            and args[2].lower() == "of"
        ):
            rest = args[3:]

        seen: dict[str, None] = {}
        for word in rest:
            if word.lower() in Intent._STOP_WORDS:
                continue
            for path in self._path_resolver.resolve_paths(self._directory_context, word):
                seen[path] = None
        candidates = list(seen)
        first_query = next((w for w in rest if w.lower() not in Intent._STOP_WORDS), None)

        if not candidates:
            self._handle_not_found(verb, first_query)
            raise UserCancelled

        resolved = self._source_selector.select(candidates, self._directory_context, query=first_query)
        self._console.confirm_action(verb, self._console.abs_path(resolved))
        return f"{verb} {resolved}"

    def _handle_not_found(self, verb, term) -> None:
        if self._console.yes or self._console.dry_run:
            raise UserCancelled
        selection = self._disambiguator.pick_not_found(term=None)
        self._run_with_args_fn([selection.value])
