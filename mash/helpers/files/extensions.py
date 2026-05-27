import os
from collections import Counter
from pathlib import Path


class Extensions:
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

    @classmethod
    def from_prompt(cls, arguments: list[str]) -> str | None:
        for token in arguments:
            extension = cls.EXTENSION_MAP.get(token.lower())
            if extension:
                return extension
        return None

    @classmethod
    def collect(cls, directory_context: str) -> list[str]:
        counts: Counter = Counter()
        for line in directory_context.splitlines():
            path = Path(line.strip())
            if path.suffix:
                counts[path.suffix.lstrip(".").lower()] += 1
        return [extension for extension, _ in counts.most_common()]

    @classmethod
    def format_filename(cls, raw_name: str, extension: str) -> list[str]:
        words = raw_name.lower().split()
        snake = "_".join(words) + extension
        kebab = "-".join(words) + extension
        camel = words[0] + "".join(word.capitalize() for word in words[1:]) + extension
        return [snake, kebab, camel]

    @classmethod
    def reconcile_rename(cls, before_path: str, after_token: str) -> tuple[str, str | None]:
        before_extension = os.path.splitext(before_path)[1]
        after_extension = os.path.splitext(after_token)[1]
        if after_extension == "" and before_extension != "":
            return after_token + before_extension, None
        if after_extension.lower() == before_extension.lower():
            return after_token, None
        if before_extension != "" and after_extension != "":
            return after_token, "different_extension"
        return after_token, "add_extension"
