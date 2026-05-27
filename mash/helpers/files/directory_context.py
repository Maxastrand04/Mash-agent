import subprocess


class DirectoryContext:
    @classmethod
    def get(cls) -> str:
        result = subprocess.run(
            ["find", ".", "-maxdepth", "4", "-not", "-path", "*/.*"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
