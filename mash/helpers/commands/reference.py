COMMANDS: dict[str, str] = {
    "ls":    "list files in a directory",
    "cd":    "navigate into a subdirectory",
    "mv":    "move or rename a file",
    "cp":    "copy a file or directory",
    "rm":    "delete a file or directory",
    "mkdir": "create a new directory",
    "find":  "search for files by name or pattern",
    "open":  "open a file with its default application",
    "cat":   "print file contents to the terminal",
    "touch": "create a new empty file",
    "chmod": "change file permissions",
}

formatted = "\n".join(f"  {cmd}: {desc}" for cmd, desc in COMMANDS.items())
