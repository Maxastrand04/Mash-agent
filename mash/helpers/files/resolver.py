import difflib
from pathlib import Path


def resolve_paths(tree: str, term: str) -> list[str]:
    """Fuzzy-match a term against file stems in a directory tree.

    Uses difflib's close-match heuristic against path stems (not full
    paths) so users can refer to "report" and hit "report.md" without
    typing the extension. Results are ordered by depth so shallow hits
    win — they're usually the user's intent.

    Args:
        tree: Newline-delimited directory tree.
        term: User-typed search term.

    Returns:
        Up to ~5 matching paths, deduplicated and shallow-first.

    Raises:
        None.
    """
    paths = [line.strip() for line in tree.splitlines() if line.strip()]
    stems: dict[str, list[str]] = {}
    for p in paths:
        stem = Path(p).stem.lower()
        stems.setdefault(stem, []).append(p)
    matches = difflib.get_close_matches(term.lower(), stems.keys(), n=5, cutoff=0.6)
    result = []
    for m in matches:
        for p in stems[m]:
            if p not in result:
                result.append(p)
    result.sort(key=lambda p: p.count("/"))
    return result


def resolve_dirs(tree: str, term: str) -> list[str]:
    """Same as resolve_paths but restricted to directory entries.

    A path with no suffix is treated as a directory — the find-based
    tree contains both, and we use the absence of an extension as a
    cheap proxy rather than stat-ing each path.

    Args:
        tree: Newline-delimited directory tree.
        term: User-typed search term.

    Returns:
        Up to ~5 matching directory paths, deduplicated and shallow-first.

    Raises:
        None.
    """
    paths = [line.strip() for line in tree.splitlines() if line.strip()]
    dir_stems: dict[str, list[str]] = {}
    for p in paths:
        path = Path(p)
        if path.suffix == "" and p != ".":
            stem = path.stem.lower()
            dir_stems.setdefault(stem, []).append(p)
    matches = difflib.get_close_matches(term.lower(), dir_stems.keys(), n=5, cutoff=0.6)
    result = []
    for m in matches:
        for p in dir_stems[m]:
            if p not in result:
                result.append(p)
    result.sort(key=lambda p: p.count("/"))
    return result
