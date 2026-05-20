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
    for w in args:
        ext = EXTENSION_MAP.get(w.lower())
        if ext:
            return ext
    return None


def collect_extensions(context: str) -> list[str]:
    counts: Counter = Counter()
    for line in context.splitlines():
        p = Path(line.strip())
        if p.suffix:
            counts[p.suffix.lstrip(".").lower()] += 1
    return [ext for ext, _ in counts.most_common()]


def format_filename(raw_name: str, extension: str) -> list[str]:
    words = raw_name.lower().split()
    snake = "_".join(words) + extension
    kebab = "-".join(words) + extension
    camel = words[0] + "".join(w.capitalize() for w in words[1:]) + extension
    return [snake, kebab, camel]


def reconcile_rename_extension(before_path: str, after_token: str) -> tuple[str, str | None]:
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
