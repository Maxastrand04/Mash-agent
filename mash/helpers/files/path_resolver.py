import difflib
from pathlib import Path


class PathResolver:
    @classmethod
    def resolve_paths(cls, directory_context: str, term: str) -> list[str]:
        paths = [line.strip() for line in directory_context.splitlines() if line.strip()]
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

    @classmethod
    def resolve_dirs(cls, directory_context: str, term: str) -> list[str]:
        paths = [line.strip() for line in directory_context.splitlines() if line.strip()]
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
