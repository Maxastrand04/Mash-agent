import re
from dataclasses import dataclass


_STOP_WORDS = {
    "move", "copy", "duplicate", "clone", "replicate",
    "rename", "delete", "remove", "list", "create", "make",
    "open", "show", "get", "put", "add", "find",
    "to", "the", "a", "an", "in", "into", "from", "of", "and", "or",
    "inside", "under", "called", "named",
    "file", "files", "folder", "folders", "directory", "dir",
    "all", "new", "old", "my", "its", "current",
}

_RENAME_VERBS = {
    "rename", "change name", "alter name", "swap name", "relabel",
    "rebrand", "retitle", "reassign name", "give new name",
}

_LIST_TRIGGERS = {"list", "ls"}
_OPEN_TRIGGERS = {"open"}
_CAT_TRIGGERS = {"cat", "print"}

_ARTICLES = {"the", "a", "an", "this", "that"}
_FILENAME_RE = re.compile(r'^[A-Za-z0-9_\-]+\.[A-Za-z0-9]{1,10}$')


@dataclass
class Intent:
    """Parsed user request, normalized into verb + structured args.

    Centralizing intent shape here keeps the flow modules free of raw
    token-parsing — they receive a pre-classified Intent and only need
    to consume the fields relevant to their verb.
    """

    verb: str
    args: list[str]
    filtered_args: list[str]
    dest_token: str | None
    rename_target: str | None
    is_create_file: bool
    is_create_folder: bool


def _looks_like_filename(token: str) -> bool:
    """Heuristic check for stem.ext-shaped tokens.

    The regex matches `name.ext` where ext is 1-10 alphanumerics — wide
    enough for common extensions but tight enough to reject IPs, version
    strings, and sentence fragments.

    Args:
        token: Single argument token to test.

    Returns:
        True when the token matches the filename regex.

    Raises:
        None.
    """
    return bool(_FILENAME_RE.match(token))


def _find_rename_verb_start(args: list[str]) -> int | None:
    """Locate the latest rename-verb phrase in args.

    Returns the latest match so prompts like "move foo to bar then
    rename it to baz" treat the trailing rename as authoritative.

    Args:
        args: Tokenized prompt.

    Returns:
        Start index of the latest matching rename phrase, or None.

    Raises:
        None.
    """
    lower = [a.lower() for a in args]
    last_idx = None
    for phrase in _RENAME_VERBS:
        tokens = phrase.split()
        n = len(tokens)
        for i in range(len(lower) - n + 1):
            if lower[i:i + n] == tokens:
                if last_idx is None or i > last_idx:
                    last_idx = i
    return last_idx


def _detect_rename_intent(args: list[str]) -> bool:
    """Test whether the prompt contains any known rename phrase.

    Uses a substring check against the joined args so multi-word phrases
    like "change name" match regardless of token boundaries.

    Args:
        args: Tokenized prompt.

    Returns:
        True when a rename phrase is present.

    Raises:
        None.
    """
    joined = " ".join(args).lower()
    return any(phrase in joined for phrase in _RENAME_VERBS)


def _extract_rename_target(args: list[str]) -> str | None:
    """Extract the new name following the final "to" after a rename verb.

    Looks only at "to" markers occurring at or after the rename verb so
    earlier "to" markers (e.g. a move destination) don't get misread as
    the new name.

    Args:
        args: Tokenized prompt.

    Returns:
        The token after the latest "to", or None when no rename or no
        target token is present.

    Raises:
        None.
    """
    rename_start = _find_rename_verb_start(args)
    if rename_start is None:
        return None
    lower = [a.lower() for a in args]
    last_to = None
    for i in range(rename_start, len(lower)):
        if lower[i] == "to":
            last_to = i
    if last_to is None or last_to + 1 >= len(args):
        return None
    return args[last_to + 1]


def _detect_destination_idx(args: list[str]) -> int | None:
    """Find the destination token following a preposition marker.

    Skips intervening articles ("the", "a", …) so "move foo to the bar
    folder" still points at "bar".

    Args:
        args: Tokenized prompt.

    Returns:
        Index of the destination token, or None when no marker is found.

    Raises:
        None.
    """
    markers = {"to", "into", "inside", "in"}
    for i, word in enumerate(args):
        if word.lower() in markers:
            j = i + 1
            while j < len(args) and args[j].lower() in _ARTICLES:
                j += 1
            if j < len(args):
                return j
    return None


def _detect_destination_idx_before_rename(args: list[str]) -> int | None:
    """Like _detect_destination_idx but stops at the rename verb.

    Prevents the "to" inside "rename X to Y" from being misread as a
    move destination — the destination must appear before the rename
    verb to count.

    Args:
        args: Tokenized prompt.

    Returns:
        Destination index strictly before the rename verb, or None.

    Raises:
        None.
    """
    rename_start = _find_rename_verb_start(args)
    if rename_start is None:
        return _detect_destination_idx(args)
    markers = {"to", "into", "inside", "in"}
    for i, word in enumerate(args):
        if i >= rename_start:
            break
        if word.lower() in markers:
            j = i + 1
            while j < len(args) and j < rename_start and args[j].lower() in _ARTICLES:
                j += 1
            if j < len(args) and j < rename_start:
                return j
    return None


def _detect_new_filename(args: list[str]) -> tuple[str, str] | None:
    """Extract a (raw_name, extension) tuple from a "create … named X" prompt.

    Two-token minimum on the raw name is enforced so single-word names
    fall through to the bare-create branch (which has its own filename
    format menu).

    Args:
        args: Tokenized prompt.

    Returns:
        (raw_name, extension) where extension has a leading dot or is
        empty; None when no "called"/"named" marker is present or the
        name is too short.

    Raises:
        None.
    """
    create_words = {"create", "make"}
    if not args or args[0].lower() not in create_words:
        return None
    markers = {"called", "named"}
    marker_idx = next((i for i, w in enumerate(args) if w.lower() in markers), None)
    if marker_idx is None or marker_idx + 1 >= len(args):
        return None
    name_tokens = []
    extension = ""
    for token in args[marker_idx + 1:]:
        if "." in token:
            parts = token.rsplit(".", 1)
            name_tokens.append(parts[0])
            extension = f".{parts[1]}"
            break
        name_tokens.append(token)
    if not extension:
        from mash.helpers.files import EXTENSION_MAP
        for word in args:
            if word.lower() in EXTENSION_MAP:
                extension = EXTENSION_MAP[word.lower()]
                break
    raw_name = " ".join(name_tokens)
    if len(name_tokens) < 2:
        return None
    return raw_name, extension


def _is_list_intent(args: list[str]) -> bool:
    """Detect listing prompts.

    Recognizes both verb-first forms ("list …", "ls …") and natural
    paraphrases ("show files in …", "show contents …") so users get
    the listing flow without having to memorize the verb.

    Args:
        args: Tokenized prompt.

    Returns:
        True when the prompt should route to list_flow.

    Raises:
        None.
    """
    if not args:
        return False
    if args[0].lower() in _LIST_TRIGGERS:
        return True
    joined = " ".join(a.lower() for a in args)
    return joined.startswith("show files") or joined.startswith("show contents")


def _is_open_intent(args: list[str]) -> bool:
    """Detect open-with-system-handler prompts.

    Args:
        args: Tokenized prompt.

    Returns:
        True when the prompt starts with an open trigger word.

    Raises:
        None.
    """
    return bool(args) and args[0].lower() in _OPEN_TRIGGERS


def _is_cat_intent(args: list[str]) -> bool:
    """Detect file-printing prompts.

    "show contents of" overlaps with the listing detector ("show
    contents"); cat is checked first in parse_intent so this stays a
    safe-by-order heuristic rather than requiring lookbehind.

    Args:
        args: Tokenized prompt.

    Returns:
        True when the prompt should route to cat in open_cat_flow.

    Raises:
        None.
    """
    if not args:
        return False
    if args[0].lower() in _CAT_TRIGGERS:
        return True
    joined = " ".join(a.lower() for a in args)
    return joined.startswith("show contents of")


def parse_intent(args: list[str]) -> Intent:
    """Classify a tokenized prompt into a structured Intent.

    Verb-detection order matters: cat is checked before list because
    "show contents" prefixes both; the remaining branches fall through
    to a heuristic based on the first verb. This function is pure — no
    I/O, no filesystem access — so it can be unit-tested in isolation.

    Args:
        args: Tokenized user prompt (CLI argv minus flags).

    Returns:
        A populated Intent. The verb defaults to "other" when nothing
        matches, which main.py treats as move/copy fallthrough.

    Raises:
        None.
    """
    if _is_cat_intent(args):
        return Intent(
            verb="cat", args=args, filtered_args=args,
            dest_token=None, rename_target=None,
            is_create_file=False, is_create_folder=False,
        )

    if _is_list_intent(args):
        return Intent(
            verb="list", args=args, filtered_args=args,
            dest_token=None, rename_target=None,
            is_create_file=False, is_create_folder=False,
        )

    if _is_open_intent(args):
        return Intent(
            verb="open", args=args, filtered_args=args,
            dest_token=None, rename_target=None,
            is_create_file=False, is_create_folder=False,
        )

    is_rename = _detect_rename_intent(args)
    rename_target: str | None = None

    if is_rename:
        rename_target = _extract_rename_target(args)
        dest_idx = _detect_destination_idx_before_rename(args)
    else:
        dest_idx = _detect_destination_idx(args)

    dest_token = args[dest_idx] if dest_idx is not None else None

    is_create_form = bool(args) and args[0].lower() in {"create", "make"}
    has_file_word = is_create_form and any(w.lower() == "file" for w in args)
    has_folder_word = is_create_form and any(w.lower() in {"directory", "folder", "dir"} for w in args)
    is_create_file = has_file_word
    is_create_folder = has_folder_word

    # Detect bare create with filename pattern
    create_bare_path: str | None = None
    if is_create_form and not has_file_word and not has_folder_word:
        candidate_tokens = [
            (i, w) for i, w in enumerate(args)
            if i != 0 and i != dest_idx and w.lower() not in _STOP_WORDS
        ]
        filename_tokens = [(i, w) for i, w in candidate_tokens if _looks_like_filename(w)]
        if filename_tokens:
            is_create_file = True

    filtered_args: list[str] = []
    skip_rest = False
    for i, w in enumerate(args):
        if skip_rest:
            continue
        if i == dest_idx:
            continue
        if is_create_form and w.lower() in {"called", "named"}:
            skip_rest = True
            continue
        filtered_args.append(w)

    if is_rename:
        verb = "rename"
    elif is_create_file or is_create_folder:
        verb = "create"
    elif is_create_form:
        verb = "create"
    else:
        _move_verbs = {"move"}
        _copy_verbs = {"copy", "duplicate", "clone", "replicate"}
        first = args[0].lower() if args else ""
        if first in {"delete", "remove"}:
            verb = "delete"
        elif first in _move_verbs:
            verb = "move"
        elif first in _copy_verbs:
            verb = "copy"
        else:
            verb = "other"

    return Intent(
        verb=verb,
        args=args,
        filtered_args=filtered_args,
        dest_token=dest_token,
        rename_target=rename_target,
        is_create_file=is_create_file,
        is_create_folder=is_create_folder,
    )
