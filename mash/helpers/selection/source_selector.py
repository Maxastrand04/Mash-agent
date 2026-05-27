from mash.exceptions.source_not_found import SourceNotFound
from mash.helpers.files.path_resolver import PathResolver


class SourceSelector:
    def __init__(self, console, disambiguator):
        self.console = console
        self.disambiguator = disambiguator

    def select(
        self,
        candidates: list[str],
        directory_context: str,
        query: str | None = None,
    ) -> str:
        if self.console.yes or self.console.dry_run:
            if not candidates:
                raise SourceNotFound(query or "<no query>")
            prefix = "[dry-run] " if self.console.dry_run else ""
            print(f"\n{prefix}Auto-selected: {candidates[0]}")
            return candidates[0]

        while True:
            if not candidates:
                selection = self.disambiguator.pick_not_found(term=query)
                query = selection.value
                candidates = PathResolver.resolve_paths(directory_context, selection.value)
                continue

            selection = self.disambiguator.pick_from_hits(
                hits=candidates, term=query, kind="file"
            )
            if selection.kind == "selected":
                return selection.value
            query = selection.value
            candidates = PathResolver.resolve_paths(directory_context, selection.value)
