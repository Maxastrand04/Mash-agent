import re
from dataclasses import dataclass


@dataclass
class Intent:
    verb: str
    args: list[str]
    filtered_args: list[str]
    dest_token: str | None
    rename_target: str | None
    is_create_file: bool
    is_create_folder: bool

    _STOP_WORDS = {
        "move", "copy", "duplicate", "clone", "replicate",
        "rename", "delete", "remove", "list", "create", "make",
        "open", "show", "get", "put", "add", "find",
        "to", "the", "a", "an", "in", "into", "from", "of", "and", "or",
        "inside", "under", "called", "named",
        "file", "files", "folder", "folders", "directory", "dir",
        "all", "new", "old", "my", "its", "current",
    }

    _RENAME_VERBS = (
        "rename", "change name", "alter name", "swap name", "relabel",
        "rebrand", "retitle", "reassign name", "give new name",
    )

    _LIST_TRIGGERS = {"list", "ls"}
    _OPEN_TRIGGERS = {"open"}
    _CAT_TRIGGERS = {"cat", "print"}
    _ARTICLES = {"the", "a", "an", "this", "that"}
    _FILENAME_RE = re.compile(r'^[A-Za-z0-9_\-]+\.[A-Za-z0-9]{1,10}$')

    @classmethod
    def parse(cls, args: list[str]) -> "Intent":
        if cls._is_cat_intent(args):
            return cls(
                verb="cat", args=args, filtered_args=args,
                dest_token=None, rename_target=None,
                is_create_file=False, is_create_folder=False,
            )

        if cls._is_list_intent(args):
            return cls(
                verb="list", args=args, filtered_args=args,
                dest_token=None, rename_target=None,
                is_create_file=False, is_create_folder=False,
            )

        if cls._is_open_intent(args):
            return cls(
                verb="open", args=args, filtered_args=args,
                dest_token=None, rename_target=None,
                is_create_file=False, is_create_folder=False,
            )

        is_rename = cls._detect_rename_intent(args)
        rename_target: str | None = None

        if is_rename:
            rename_target = cls._extract_rename_target(args)
            dest_idx = cls._detect_destination_idx_before_rename(args)
        else:
            dest_idx = cls._detect_destination_idx(args)

        dest_token = args[dest_idx] if dest_idx is not None else None

        is_create_form = bool(args) and args[0].lower() in {"create", "make"}
        has_file_word = is_create_form and any(w.lower() == "file" for w in args)
        has_folder_word = is_create_form and any(w.lower() in {"directory", "folder", "dir"} for w in args)
        is_create_file = has_file_word
        is_create_folder = has_folder_word

        if is_create_form and not has_file_word and not has_folder_word:
            candidate_tokens = [
                (i, w) for i, w in enumerate(args)
                if i != 0 and i != dest_idx and w.lower() not in cls._STOP_WORDS
            ]
            filename_tokens = [(i, w) for i, w in candidate_tokens if cls._looks_like_filename(w)]
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
        elif is_create_file or is_create_folder or is_create_form:
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

        return cls(
            verb=verb,
            args=args,
            filtered_args=filtered_args,
            dest_token=dest_token,
            rename_target=rename_target,
            is_create_file=is_create_file,
            is_create_folder=is_create_folder,
        )

    @classmethod
    def _looks_like_filename(cls, token: str) -> bool:
        return bool(cls._FILENAME_RE.match(token))

    @classmethod
    def _find_rename_verb_start(cls, args: list[str]) -> int | None:
        lower = [a.lower() for a in args]
        last_idx = None
        for phrase in cls._RENAME_VERBS:
            tokens = phrase.split()
            n = len(tokens)
            for i in range(len(lower) - n + 1):
                if lower[i:i + n] == tokens:
                    if last_idx is None or i > last_idx:
                        last_idx = i
        return last_idx

    @classmethod
    def _detect_rename_intent(cls, args: list[str]) -> bool:
        joined = " ".join(args).lower()
        return any(phrase in joined for phrase in cls._RENAME_VERBS)

    @classmethod
    def _extract_rename_target(cls, args: list[str]) -> str | None:
        rename_start = cls._find_rename_verb_start(args)
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

    @classmethod
    def _detect_destination_idx(cls, args: list[str]) -> int | None:
        markers = {"to", "into", "inside", "in"}
        for i, word in enumerate(args):
            if word.lower() in markers:
                j = i + 1
                while j < len(args) and args[j].lower() in cls._ARTICLES:
                    j += 1
                if j < len(args):
                    return j
        return None

    @classmethod
    def _detect_destination_idx_before_rename(cls, args: list[str]) -> int | None:
        rename_start = cls._find_rename_verb_start(args)
        if rename_start is None:
            return cls._detect_destination_idx(args)
        markers = {"to", "into", "inside", "in"}
        for i in range(rename_start):
            word = args[i]
            if word.lower() in markers:
                j = i + 1
                while j < len(args) and j < rename_start and args[j].lower() in cls._ARTICLES:
                    j += 1
                if j < len(args) and j < rename_start:
                    return j
        return None

    @classmethod
    def _detect_new_filename(cls, args: list[str]) -> tuple[str, str] | None:
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
            from mash.helpers.files.extensions import Extensions
            for word in args:
                if word.lower() in Extensions.EXTENSION_MAP:
                    extension = Extensions.EXTENSION_MAP[word.lower()]
                    break
        raw_name = " ".join(name_tokens)
        if len(name_tokens) < 2:
            return None
        return raw_name, extension

    @classmethod
    def _is_list_intent(cls, args: list[str]) -> bool:
        if not args:
            return False
        if args[0].lower() in cls._LIST_TRIGGERS:
            return True
        joined = " ".join(a.lower() for a in args)
        return joined.startswith("show files") or joined.startswith("show contents")

    @classmethod
    def _is_open_intent(cls, args: list[str]) -> bool:
        return bool(args) and args[0].lower() in cls._OPEN_TRIGGERS

    @classmethod
    def _is_cat_intent(cls, args: list[str]) -> bool:
        if not args:
            return False
        if args[0].lower() in cls._CAT_TRIGGERS:
            return True
        joined = " ".join(a.lower() for a in args)
        return joined.startswith("show contents of")
