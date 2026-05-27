import os
import re


class CommandSanitizer:
    _LABEL_TO_SHELL_COMMAND = {
        "move_file": "mv",
        "move_folder": "mv",
        "copy_file": "cp",
        "copy_folder": "cp -r",
        "delete_file": "rm",
        "delete_folder": "rm -rf",
        "create_file": "touch",
        "create_folder": "mkdir -p",
    }

    @staticmethod
    def normalize_template_verb(command: str) -> str:
        parts = command.split(None, 1)
        if parts and parts[0] in CommandSanitizer._LABEL_TO_SHELL_COMMAND:
            replacement = CommandSanitizer._LABEL_TO_SHELL_COMMAND[parts[0]]
            return replacement + (" " + parts[1] if len(parts) > 1 else "")
        return command

    @staticmethod
    def apply_source(command: str, resolved_source: str) -> str:
        if resolved_source in command:
            return command
        parts = command.split()
        if not parts:
            return command
        verb = parts[0]
        if verb in {"mv", "cp"}:
            for i in range(1, len(parts)):
                if not parts[i].startswith("-"):
                    parts[i] = resolved_source
                    return " ".join(parts)
        elif verb in {"rm", "rmdir"}:
            parts[-1] = resolved_source
            return " ".join(parts)
        return command

    @staticmethod
    def apply_destination(command: str, destination: str) -> str:
        if "&&" in command:
            segments = [s.strip() for s in command.split("&&")]
            parts = segments[-1].split()
            if parts and parts[0] in {"mv", "cp"}:
                parts[-1] = destination.rstrip("/") + "/"
                segments[-1] = " ".join(parts)
            return " && ".join(segments)
        parts = command.split()
        if not parts or parts[0] not in {"mv", "cp"}:
            return command
        parts[-1] = destination.rstrip("/") + "/"
        return " ".join(parts)

    @staticmethod
    def apply_rename(command: str, before_path: str, after_path: str, destination: str | None = None) -> str:
        parts = command.split()
        if not parts or parts[0] != "mv":
            return command
        for i in range(1, len(parts)):
            if not parts[i].startswith("-"):
                parts[i] = before_path
                break
        if destination:
            parts[-1] = destination.rstrip("/") + "/" + after_path
        else:
            if "/" in after_path:
                parts[-1] = after_path if after_path.startswith("./") else f"./{after_path}"
            else:
                parent = os.path.dirname(before_path)
                if parent and parent not in (".", "./"):
                    parts[-1] = f"{parent.rstrip('/')}/{after_path}"
                else:
                    parts[-1] = after_path if after_path.startswith("./") else f"./{after_path}"
        return " ".join(parts)

    @staticmethod
    def apply_filename(command: str, raw_name: str, filename: str, destination: str | None = None) -> str:
        pattern = re.escape(raw_name).replace(r"\ ", r"\\?\s")
        pattern = rf"\.?/?(?:{pattern})(\.[A-Za-z0-9]+)?"
        if destination and destination not in (".", "./"):
            new = f"{destination.rstrip('/')}/{filename}"
        else:
            new = f"./{filename}"
        if re.search(pattern, command):
            return re.sub(pattern, new, command, count=1)
        parts = command.split()
        if parts and parts[0] in {"touch", "mkdir"}:
            parts[-1] = new
            return " ".join(parts)
        return command

    @staticmethod
    def strip_recursive_flags(command: str, source_type: str) -> str:
        if source_type in ("file", "unknown"):
            command = re.sub(r'\brm\s+-rf\b', 'rm', command)
            command = re.sub(r'\bcp\s+-r\b', 'cp', command)
        return command
