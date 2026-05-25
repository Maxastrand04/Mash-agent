import subprocess


def get_directory_context() -> str:
    """Snapshot the current directory tree for LLM prompts and resolvers.

    Limited to depth 4 to keep the prompt budget bounded; dotfiles are
    excluded so VCS and editor metadata never leak into the context.

    Returns:
        Newline-delimited list of paths under cwd.

    Raises:
        None.
    """
    result = subprocess.run(
        ["find", ".", "-maxdepth", "4", "-not", "-path", "*/.*"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
