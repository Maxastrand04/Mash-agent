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
    parts = cmd.split(None, 1)
    if parts and parts[0] in _LABEL_TO_CMD:
        replacement = _LABEL_TO_CMD[parts[0]]
        return replacement + (" " + parts[1] if len(parts) > 1 else "")
    return cmd


def apply_source(cmd: str, resolved: str) -> str:
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
    if source_type in ("file", "unknown"):
        cmd = re.sub(r'\brm\s+-rf\b', 'rm', cmd)
        cmd = re.sub(r'\bcp\s+-r\b', 'cp', cmd)
    return cmd
