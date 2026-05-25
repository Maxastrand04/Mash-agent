import os
from mash.helpers.files import resolve_paths
from mash.helpers.selection import select_source
from mash.helpers.commands import normalize_template_verb, apply_source, strip_recursive_flags
from mash.intent import _STOP_WORDS


def delete_flow(intent, console, llm, disambig, context) -> str | None:
    """Orchestrate the delete intent.

    Resolves source candidates from the filtered args, asks the LLM for a
    delete command, sanitizes recursive flags so a stray `-r` on a file
    deletion doesn't escalate scope, and returns the command together with
    the absolute path being deleted so confirm-and-run can highlight what
    is about to disappear.

    Args:
        intent: Parsed Intent describing the user request.
        console: Console helper for prompts and I/O.
        llm: LLMClient used to translate the prompt to a shell command.
        disambig: Disambiguation strategy passed through to selection.
        context: Directory tree string supplied to the LLM and resolvers.

    Returns:
        A (command, delete_path) tuple where delete_path is the resolved
        target for plain `rm` commands, otherwise None. Returns None
        outright if the user cancels or the LLM returns nothing.

    Raises:
        None.
    """
    seen: dict[str, None] = {}
    for word in intent.filtered_args:
        if word.lower() not in _STOP_WORDS:
            for p in resolve_paths(context, word):
                seen[p] = None
    source_candidates = list(seen)

    source_query = next(
        (w for w in intent.filtered_args if w.lower() not in _STOP_WORDS), None
    )
    resolved = select_source(source_candidates, context, console, disambig, query=source_query)
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
