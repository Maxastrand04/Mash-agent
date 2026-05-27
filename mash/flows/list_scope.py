import os
import subprocess

from mash.helpers.files import PathResolver
from mash.intent import Intent


class ListScope:
    @staticmethod
    def scope_label(scope: str) -> str:
        cwd = os.getcwd()
        abs_scope = os.path.abspath(scope)
        if abs_scope == cwd:
            return "."
        rel = os.path.relpath(abs_scope, start=cwd)
        if rel.startswith(".."):
            return abs_scope
        return f"./{rel}"

    @staticmethod
    def scoped_context(scope: str) -> str:
        result = subprocess.run(
            ["find", scope, "-maxdepth", "4", "-not", "-path", "*/.*"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    @staticmethod
    def list_entries(scope: str) -> list[tuple[str, bool]]:
        try:
            entries = sorted(os.listdir(scope))
        except OSError:
            return []
        entries = [e for e in entries if not e.startswith(".")]
        result = []
        for name in entries:
            full = os.path.join(scope, name)
            result.append((full, os.path.isdir(full)))
        return result

    @staticmethod
    def list_target_from_arguments(arguments: list[str], directory_context: str) -> str:
        markers = {"in", "inside", "of", "from"}
        for i, w in enumerate(arguments):
            if w.lower() in markers and i + 1 < len(arguments):
                tok = arguments[i + 1]
                candidates = PathResolver.resolve_dirs(directory_context, tok)
                if candidates:
                    return candidates[0]
        for w in arguments:
            if w.lower() in Intent._STOP_WORDS:
                continue
            candidates = PathResolver.resolve_dirs(directory_context, w)
            if candidates:
                return candidates[0]
        return "."
