SEARCH_AGAIN_OPTION = "search for another file"
SEARCH_FOOTER = "Type a filename to search, Enter to cancel:"


class Disambig:
    """Picker UI for ambiguous resolver results.

    Exposes three shapes — pick_from_hits (numbered candidates),
    pick_not_found (free-text retry), pick_with_actions (hits plus
    named follow-up actions) — so flow code can compose them without
    re-implementing menu rendering and selection parsing.
    """

    def __init__(self, console):
        """Bind the picker to a Console instance.

        Args:
            console: Console used for menu rendering and input.

        Returns:
            None.

        Raises:
            None.
        """
        self.console = console

    def _prompt(self, header: str, options: list[str], footer: str) -> str:
        """Render a menu and read one line of input.

        Args:
            header: Menu title.
            options: Display labels.
            footer: Prompt shown below the options.

        Returns:
            The user's raw input.

        Raises:
            None.
        """
        prompt_str = self.console.render_menu(header, options, footer)
        return self.console.ask_input(prompt_str)

    @staticmethod
    def _parse_selection(answer: str, n: int) -> int | None:
        """Parse a 1-based menu choice and validate the range.

        Args:
            answer: Raw input string.
            n: Number of valid options.

        Returns:
            Zero-based index, or None when the input is non-numeric or
            out of range (so the caller can treat it as a typed prompt).

        Raises:
            None.
        """
        try:
            idx = int(answer) - 1
        except ValueError:
            return None
        if 0 <= idx < n:
            return idx
        return None

    def pick_from_hits(
        self,
        hits: list[str],
        term: str | None = None,
        kind: str = "file",
    ) -> tuple[str, object]:
        """Show numbered hits and read either a selection or a typed term.

        Args:
            hits: Candidate paths to display.
            term: Optional search term used in the header.
            kind: "file" or "folder" — used in header phrasing.

        Returns:
            ("cancelled", None) on empty input, ("selected", path) on a
            valid numeric pick, or ("typed", value) when the user typed
            a fresh search term.

        Raises:
            None.
        """
        n = len(hits)
        term_label = f" for '{term}'" if term else ""
        if n == 1:
            header = f"Mash found a {kind}{term_label}:"
        else:
            header = f"Mash found {n} {kind}s{term_label}:"
        options = [self.console.abs_path(p) for p in hits]
        range_label = "1" if n == 1 else f"1-{n}"
        footer = f"Select option [{range_label}], Enter to cancel, type another prompt:"
        answer = self._prompt(header, options, footer)
        if not answer:
            return ("cancelled", None)
        idx = self._parse_selection(answer, n)
        if idx is not None:
            return ("selected", hits[idx])
        return ("typed", answer)

    def pick_not_found(
        self,
        term: str | None = None,
    ) -> tuple[str, object]:
        """Prompt for a fresh search term after a failed lookup.

        Args:
            term: Original search term that returned no hits, for the header.

        Returns:
            ("cancelled", None) on empty input, or ("typed", value) with
            the user's retry term.

        Raises:
            None.
        """
        q_label = f" for '{term}'" if term else ""
        header = f"Mash did not find a matching file{q_label}, choose how to proceed:"
        options: list[str] = []
        answer = self._prompt(header, options, SEARCH_FOOTER)
        if not answer:
            return ("cancelled", None)
        return ("typed", answer)

    def pick_with_actions(
        self,
        hits: list[str],
        actions: list[tuple[str, str]],
        header: str,
        display: list[str] | None = None,
    ) -> tuple[str, object]:
        """Show hits followed by named actions, returning whichever was picked.

        Used by select_destination to offer "create here" or "select cwd"
        alongside resolver candidates, in a single numbered menu.

        Args:
            hits: Candidate paths displayed first.
            actions: (label, key) pairs displayed after the hits.
            header: Menu header text.
            display: Optional override for hit labels (used when paths
                need to be relabelled, e.g. "." → "(Current directory)").

        Returns:
            ("cancelled", None), ("selected", path), ("action", key), or
            ("typed", value) for free-text input.

        Raises:
            None.
        """
        hit_labels = display if display is not None else [self.console.abs_path(p) for p in hits]
        action_labels = [label for label, _ in actions]
        options = hit_labels + action_labels
        n_total = len(options)
        n_hits = len(hits)
        range_label = "1" if n_total == 1 else f"1-{n_total}"
        footer = f"Select option [{range_label}], Enter to cancel, type another prompt:"
        answer = self._prompt(header, options, footer)
        if not answer:
            return ("cancelled", None)
        idx = self._parse_selection(answer, n_total)
        if idx is None:
            return ("typed", answer)
        if idx < n_hits:
            return ("selected", hits[idx])
        return ("action", actions[idx - n_hits][1])
