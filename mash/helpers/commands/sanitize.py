import os
import re


_LABEL_TO_CMD = {
    "move_file": "mv",
    "move_folder": "mv",
    "copy_file": "cp",
    "copy_folder": "cp -r",
    "delete_file": "rm",
    "delete_folder": "rm -rf",
    "create_file": "touch",
    "create_folder": "mkdir -p",
}


def normalize_template_verb(cmd: str) -> str:
    """Rewrite template-style verbs the LLM may emit back into shell verbs.

    The LLM prompt offers labels like "move_file" / "delete_folder" so it
    doesn't have to memorize flag combinations; this strips the label
    back to the real command (e.g. "rm -rf").

    Args:
        cmd: Raw command string from the LLM.

    Returns:
        Command with the first token replaced if it was a known label;
        otherwise the original string.

    Raises:
        None.
    """
    parts = cmd.split(None, 1)
    if parts and parts[0] in _LABEL_TO_CMD:
        replacement = _LABEL_TO_CMD[parts[0]]
        return replacement + (" " + parts[1] if len(parts) > 1 else "")
    return cmd


def apply_source(cmd: str, resolved: str) -> str:
    """Force the user-resolved source path into the command.

    Guarantees the operation acts on the exact path the user disambiguated
    to, even if the LLM hallucinated a different filename. No-ops when
    the resolved path is already present.

    Args:
        cmd: Command string from the LLM.
        resolved: Absolute or relative source path chosen by the user.

    Returns:
        Command with the source argument replaced, or unchanged when the
        verb doesn't take a source in the expected position.

    Raises:
        None.
    """
    if resolved in cmd:
        return cmd
    parts = cmd.split()
    if not parts:
        return cmd
    verb = parts[0]
    if verb in {"mv", "cp"}:
        for i in range(1, len(parts)):
            if not parts[i].startswith("-"):
                parts[i] = resolved
                return " ".join(parts)
    elif verb in {"rm", "rmdir"}:
        parts[-1] = resolved
        return " ".join(parts)
    return cmd


def apply_destination(cmd: str, destination: str) -> str:
    """Force the user-resolved destination into a mv/cp command.

    Walks past any prefix `mkdir && ` segment and rewrites the final
    argument of the mv/cp leg so the LLM cannot send files to a path
    the user didn't choose.

    Args:
        cmd: Command string from the LLM.
        destination: Destination directory chosen by the user.

    Returns:
        Command with the destination argument replaced, with a trailing
        slash. Unchanged when the verb is neither mv nor cp.

    Raises:
        None.
    """
    if "&&" in cmd:
        segments = [s.strip() for s in cmd.split("&&")]
        parts = segments[-1].split()
        if parts and parts[0] in {"mv", "cp"}:
            parts[-1] = destination.rstrip("/") + "/"
            segments[-1] = " ".join(parts)
        return " && ".join(segments)
    parts = cmd.split()
    if not parts or parts[0] not in {"mv", "cp"}:
        return cmd
    parts[-1] = destination.rstrip("/") + "/"
    return " ".join(parts)


def apply_rename(cmd: str, before: str, after: str, destination: str | None = None) -> str:
    """Force before/after paths into an `mv` rename command.

    When `destination` is None the new name is anchored to before's
    parent directory so renames don't accidentally move files; passing
    an explicit destination lets the caller combine rename + move.

    Args:
        cmd: Command string from the LLM (must begin with `mv`).
        before: Existing path being renamed.
        after: New filename (with or without a directory prefix).
        destination: Optional directory to relocate the renamed file into.

    Returns:
        Command with both source and target arguments rewritten, or the
        original cmd when it does not start with `mv`.

    Raises:
        None.
    """
    parts = cmd.split()
    if not parts or parts[0] != "mv":
        return cmd
    for i in range(1, len(parts)):
        if not parts[i].startswith("-"):
            parts[i] = before
            break
    if destination:
        parts[-1] = destination.rstrip("/") + "/" + after
    else:
        if "/" in after:
            parts[-1] = after if after.startswith("./") else f"./{after}"
        else:
            parent = os.path.dirname(before)
            if parent and parent not in (".", "./"):
                parts[-1] = f"{parent.rstrip('/')}/{after}"
            else:
                parts[-1] = after if after.startswith("./") else f"./{after}"
    return " ".join(parts)


def apply_filename(cmd: str, raw_name: str, filename: str, destination: str | None = None) -> str:
    """Substitute the user-chosen filename into a create command.

    The pattern matches the raw user-typed name plus an optional dot
    prefix and trailing extension, so the LLM's own filename guess
    (which may be in a different case style) gets replaced by the
    case-style the user picked from format_filename's menu.

    Args:
        cmd: Command string from the LLM.
        raw_name: Original user-typed bare name (no extension).
        filename: Chosen formatted filename (with extension).
        destination: Optional directory; when set, prepended to filename.

    Returns:
        Command with the filename argument substituted, or unchanged when
        no substitution site is found.

    Raises:
        None.
    """
    pattern = re.escape(raw_name).replace(r"\ ", r"\\?\s")
    pattern = rf"\.?/?(?:{pattern})(\.[A-Za-z0-9]+)?"
    if destination and destination not in (".", "./"):
        new = f"{destination.rstrip('/')}/{filename}"
    else:
        new = f"./{filename}"
    if re.search(pattern, cmd):
        return re.sub(pattern, new, cmd, count=1)
    parts = cmd.split()
    if parts and parts[0] in {"touch", "mkdir"}:
        parts[-1] = new
        return " ".join(parts)
    return cmd


def strip_recursive_flags(cmd: str, source_type: str) -> str:
    """Strip `-r`/`-rf` from rm/cp when the source is a file.

    Prevents the LLM from generating a recursive delete on a single
    file, which would silently succeed but signal sloppy intent — and
    would be destructive if the path later resolved to a directory.

    Args:
        cmd: Command string to clean.
        source_type: "file", "directory", or "unknown".

    Returns:
        Command with recursive flags removed for file/unknown sources;
        unchanged for directory sources.

    Raises:
        None.
    """
    if source_type in ("file", "unknown"):
        cmd = re.sub(r'\brm\s+-rf\b', 'rm', cmd)
        cmd = re.sub(r'\bcp\s+-r\b', 'cp', cmd)
    return cmd
