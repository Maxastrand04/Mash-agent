TEMPLATES: dict[str, str] = {
    "move_file":      "mv {source} {destination}",
    "move_folder":    "mv {source} {destination}",
    "rename":         "mv {before} {after}",
    "copy_file":      "cp {source} {destination}",
    "copy_folder":    "cp -r {source} {destination}",
    "delete_file":    "rm {path}",
    "delete_folder":  "rm -rf {path}",
    "create_file":    "touch {path}",
    "create_folder":  "mkdir -p {path}",
    "open":           "open {path}",
    "list":           "ls -la {path}",
    "cat":            "cat {path}",
    "chmod":          "chmod {permissions} {path}",
}

formatted = "\n".join(f"  {intent}: {cmd}" for intent, cmd in TEMPLATES.items())
