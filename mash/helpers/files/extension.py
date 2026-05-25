import os
from collections import Counter
from pathlib import Path


EXTENSION_MAP = {
    "python": ".py", "py": ".py",
    "text": ".txt", "txt": ".txt",
    "markdown": ".md", "md": ".md",
    "javascript": ".js", "js": ".js",
    "typescript": ".ts", "ts": ".ts",
    "html": ".html", "css": ".css",
    "json": ".json", "yaml": ".yaml", "yml": ".yml",
    "shell": ".sh", "bash": ".sh",
}


def extension_from_prompt(args: list[str]) -> str | None:
    """Sniff a file extension from natural-language tokens.

    Args:
        args: Tokenized user prompt (e.g. ["create", "a", "python", "file"]).

    Returns:
        The mapped extension with leading dot (e.g. ".py"), or None if
        no token matches EXTENSION_MAP.

    Raises:
        None.
    """
    for w in args:
        ext = EXTENSION_MAP.get(w.lower())
        if ext:
            return ext
    return None


def collect_extensions(context: str) -> list[str]:
    """Rank existing file extensions in a directory tree by frequency.

    Lets the create flow offer "extensions that fit this folder" as the
    first menu, so new files default to looking like their siblings.

    Args:
        context: Newline-delimited directory tree from get_directory_context.

    Returns:
        Extensions (without leading dot, lowercased) ordered by descending
        frequency.

    Raises:
        None.
    """
    counts: Counter = Counter()
    for line in context.splitlines():
        p = Path(line.strip())
        if p.suffix:
            counts[p.suffix.lstrip(".").lower()] += 1
    return [ext for ext, _ in counts.most_common()]


def format_filename(raw_name: str, extension: str) -> list[str]:
    """Render a name in snake/kebab/camel case for the picker menu.

    Args:
        raw_name: Whitespace-separated name as the user typed it.
        extension: Extension to append (with leading dot, may be empty).

    Returns:
        Three candidates in order: snake_case, kebab-case, camelCase —
        the picker shows them with these style labels alongside.

    Raises:
        None.
    """
    words = raw_name.lower().split()
    snake = "_".join(words) + extension
    kebab = "-".join(words) + extension
    camel = words[0] + "".join(w.capitalize() for w in words[1:]) + extension
    return [snake, kebab, camel]


def reconcile_rename_extension(before_path: str, after_token: str) -> tuple[str, str | None]:
    """Decide whether a rename target needs a user prompt about extensions.

    Three silent cases: after has no ext and before has one (carry it
    over), extensions match (no prompt), or both are empty. The two
    prompt cases are returned to the caller so it can ask the user.

    Args:
        before_path: Existing path being renamed.
        after_token: Proposed new name.

    Returns:
        (final_after, prompt_kind) where prompt_kind is None for silent
        cases, "different_extension" when both had different extensions,
        or "add_extension" when the new name introduces one.

    Raises:
        None.
    """
    before_ext = os.path.splitext(before_path)[1]
    after_ext = os.path.splitext(after_token)[1]
    if after_ext == "" and before_ext != "":
        return after_token + before_ext, None
    if after_ext.lower() == before_ext.lower():
        return after_token, None
    if before_ext != "" and after_ext != "":
        return after_token, "different_extension"
    if before_ext == "" and after_ext == "":
        return after_token, None
    return after_token, "add_extension"
