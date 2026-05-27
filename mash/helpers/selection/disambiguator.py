from dataclasses import dataclass

from mash.exceptions.user_cancelled import UserCancelled


@dataclass
class Selection:
    kind: str
    value: str


class Disambiguator:
    SEARCH_AGAIN_OPTION = "search for another file"
    SEARCH_FOOTER = "Type a filename to search, Enter to cancel:"

    def __init__(self, console):
        self.console = console

    def _prompt(self, header: str, options: list[str], footer: str) -> str:
        prompt_string = self.console.render_menu(header, options, footer)
        return self.console.ask_input(prompt_string)

    @staticmethod
    def _parse_selection(answer: str, option_count: int) -> int | None:
        try:
            zero_based_index = int(answer) - 1
        except ValueError:
            return None
        if 0 <= zero_based_index < option_count:
            return zero_based_index
        return None

    def pick_from_hits(
        self,
        hits: list[str],
        term: str | None = None,
        kind: str = "file",
    ) -> Selection:
        hit_count = len(hits)
        term_label = f" for '{term}'" if term else ""
        if hit_count == 1:
            header = f"Mash found a {kind}{term_label}:"
        else:
            header = f"Mash found {hit_count} {kind}s{term_label}:"
        options = [self.console.abs_path(path) for path in hits]
        range_label = "1" if hit_count == 1 else f"1-{hit_count}"
        footer = f"Select option [{range_label}], Enter to cancel, type another prompt:"
        answer = self._prompt(header, options, footer)
        if not answer:
            raise UserCancelled()
        selected_index = self._parse_selection(answer, hit_count)
        if selected_index is not None:
            return Selection(kind="selected", value=hits[selected_index])
        return Selection(kind="typed", value=answer)

    def pick_not_found(self, term: str | None = None) -> Selection:
        term_label = f" for '{term}'" if term else ""
        header = f"Mash did not find a matching file{term_label}, choose how to proceed:"
        options: list[str] = []
        answer = self._prompt(header, options, self.SEARCH_FOOTER)
        if not answer:
            raise UserCancelled()
        return Selection(kind="typed", value=answer)

    def pick_with_actions(
        self,
        hits: list[str],
        actions: list[tuple[str, str]],
        header: str,
        display: list[str] | None = None,
    ) -> Selection:
        hit_labels = display if display is not None else [self.console.abs_path(path) for path in hits]
        action_labels = [label for label, _ in actions]
        options = hit_labels + action_labels
        total_option_count = len(options)
        hit_count = len(hits)
        range_label = "1" if total_option_count == 1 else f"1-{total_option_count}"
        footer = f"Select option [{range_label}], Enter to cancel, type another prompt:"
        answer = self._prompt(header, options, footer)
        if not answer:
            raise UserCancelled()
        selected_index = self._parse_selection(answer, total_option_count)
        if selected_index is None:
            return Selection(kind="typed", value=answer)
        if selected_index < hit_count:
            return Selection(kind="selected", value=hits[selected_index])
        return Selection(kind="action", value=actions[selected_index - hit_count][1])
