import subprocess


def get_directory_context() -> str:
    result = subprocess.run(
        ["find", ".", "-maxdepth", "4", "-not", "-path", "*/.*"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
