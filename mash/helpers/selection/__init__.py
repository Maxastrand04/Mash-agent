from mash.helpers.selection.source import select_source
from mash.helpers.selection.destination import select_destination


def pick_from_disambig(hits: list[str], term: str, kind: str, console) -> str | None:
    n = len(hits)
    header = f"Mash found {n} {kind}s for '{term}':"
    options = [console.abs_path(p) for p in hits]
    footer = f"Select option [1-{n}], Enter to cancel, type another prompt:"
    prompt_str = console.render_menu(header, options, footer)
    answer = console.ask_input(prompt_str)
    if not answer:
        return None
    try:
        idx = int(answer) - 1
        if 0 <= idx < n:
            return hits[idx]
    except ValueError:
        pass
    return None
