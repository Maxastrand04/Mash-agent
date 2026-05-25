from mash.helpers.files import resolve_paths


def select_source(
    candidates: list[str], context: str, console, disambig,
    query: str | None = None,
) -> str | None:
    """Resolve a single source path, looping on not-found or typed retries.

    In yes/dry_run mode the first candidate is auto-picked (or None when
    there are no candidates, so the caller short-circuits without
    prompting). Otherwise loops until the user picks, cancels, or runs
    out of retries.

    Args:
        candidates: Initial resolver hits for the user's source token.
        context: Directory tree for retry resolutions.
        console: Console helper for yes/dry_run and printing.
        disambig: Disambiguation strategy for the picker UI.
        query: Original search term used in headers.

    Returns:
        The chosen path, or None on cancel.

    Raises:
        None.
    """
    if console.yes or console.dry_run:
        if not candidates:
            return None
        prefix = "[dry-run] " if console.dry_run else ""
        print(f"\n{prefix}Auto-selected: {candidates[0]}")
        return candidates[0]

    while True:
        if not candidates:
            kind, value = disambig.pick_not_found(term=query)
            if kind == "cancelled":
                return None
            query = value
            candidates = resolve_paths(context, value)
            continue

        kind, value = disambig.pick_from_hits(candidates, term=query, kind="file")
        if kind == "cancelled":
            return None
        if kind == "selected":
            return value
        query = value
        candidates = resolve_paths(context, value)
