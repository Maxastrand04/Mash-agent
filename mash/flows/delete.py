import os
from mash.helpers.files import resolve_paths
from mash.helpers.selection import select_source
from mash.helpers.commands import normalize_template_verb, apply_source, strip_recursive_flags
from mash.intent import _STOP_WORDS


def delete_flow(intent, console, llm, context) -> str | None:
    seen: dict[str, None] = {}
    for word in intent.filtered_args:
        if word.lower() not in _STOP_WORDS:
            for p in resolve_paths(context, word):
                seen[p] = None
    source_candidates = list(seen)

    source_query = next(
        (w for w in intent.filtered_args if w.lower() not in _STOP_WORDS), None
    )
    resolved = select_source(source_candidates, context, console, query=source_query)
    if resolved is None and not (console.yes or console.dry_run):
        print("Cancelled.")
        return None

    source_type = "unknown"
    if resolved:
        if os.path.isfile(resolved):
            source_type = "file"
        elif os.path.isdir(resolved):
            source_type = "directory"

    prompt = " ".join(intent.args)
    cmd = llm.ask(prompt, context, resolved, None, None, source_type=source_type)
    if not cmd:
        return None

    cmd = normalize_template_verb(cmd)

    if "&&" in cmd:
        segments = [s.strip() for s in cmd.split("&&")]
        non_mkdir = [s for s in segments if not s.lstrip().startswith("mkdir")]
        if non_mkdir:
            cmd = " && ".join(non_mkdir)

    cmd = strip_recursive_flags(cmd, source_type)

    if resolved:
        cmd = apply_source(cmd, resolved)

    delete_path = resolved if cmd.split()[:1] == ["rm"] and resolved else None
    return cmd, delete_path
