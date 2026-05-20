import os
import re
from mash.helpers.files import (
    resolve_paths, resolve_dirs, EXTENSION_MAP,
    extension_from_prompt, collect_extensions, format_filename,
)
from mash.helpers.selection import select_destination
from mash.helpers.commands import normalize_template_verb, apply_filename
from mash.intent import _STOP_WORDS, _looks_like_filename, _detect_new_filename


def _ask_create_kind(console) -> str | None:
    if console.yes or console.dry_run:
        return "file"
    prompt_str = console.render_menu(
        "Mash is not sure what you want to create, choose:",
        ["create file", "create folder"],
        "Select option [1-2], Enter to cancel, type another prompt:",
    )
    answer = console.ask_input(prompt_str)
    if not answer:
        return None
    if answer == "1":
        return "file"
    if answer == "2":
        return "folder"
    return None


def _pick_extension(context: str, console) -> str | None:
    dir_exts = collect_extensions(context)
    valid_set = set(dir_exts) | {v.lstrip(".") for v in EXTENSION_MAP.values()}

    while True:
        if dir_exts:
            print("\nWhat file extension?\n")
            for i, ext in enumerate(dir_exts, 1):
                print(f"  {i}. .{ext}")
            answer = console.ask_input(
                f"\nSelect extension [1-{len(dir_exts)}], type one manually (with or without dot), or Enter to cancel: "
            )
        else:
            answer = console.ask_input(
                "\nType a file extension (with or without dot), or Enter to cancel: "
            )

        if not answer:
            return None

        if dir_exts:
            try:
                idx = int(answer) - 1
                if 0 <= idx < len(dir_exts):
                    return dir_exts[idx]
            except ValueError:
                pass

        norm = answer.lstrip(".").lower()
        if not re.match(r'^[a-z0-9]{1,10}$', norm):
            print(f"Unknown extension '{norm}', try again.")
            continue
        if norm not in valid_set:
            print(f"Unknown extension '{norm}', try again.")
            continue
        return norm


def _pick_extension_auto(context: str, console) -> str | None:
    if console.yes or console.dry_run:
        exts = collect_extensions(context)
        return exts[0] if exts else "txt"
    return _pick_extension(context, console)


def create_flow(intent, console, llm, context) -> str | None:
    args = intent.args
    dest_token = intent.dest_token
    dest_idx_val = None
    for i, w in enumerate(args):
        if w == dest_token and dest_token is not None:
            dest_idx_val = i
            break

    is_create_file = intent.is_create_file
    is_create_folder = intent.is_create_folder

    create_bare_path: str | None = None
    is_create_form = bool(args) and args[0].lower() in {"create", "make"}

    if is_create_form and not intent.is_create_file and not intent.is_create_folder:
        candidate_tokens = [
            (i, w) for i, w in enumerate(args)
            if i != 0 and i != dest_idx_val and w.lower() not in _STOP_WORDS
        ]
        filename_tokens = [(i, w) for i, w in candidate_tokens if _looks_like_filename(w)]
        if filename_tokens:
            is_create_file = True
            create_bare_path = filename_tokens[0][1]
        elif candidate_tokens:
            choice = _ask_create_kind(console)
            if choice is None:
                print("Cancelled.")
                return None
            if choice == "file":
                is_create_file = True
                create_bare_path = candidate_tokens[0][1]
            else:
                is_create_folder = True
                create_bare_path = candidate_tokens[0][1]

    dest_candidates = resolve_dirs(context, dest_token) if dest_token is not None else []
    destination, create_destination = select_destination(
        dest_candidates, context, console, dest_token,
        for_create=True,
    )
    if destination is None:
        print("Cancelled.")
        return None

    filename: str | None = None
    new_file = _detect_new_filename(args)

    if is_create_file and not create_bare_path and not new_file:
        markers = {"called", "named"}
        marker_idx = next((i for i, w in enumerate(args) if w.lower() in markers), None)
        if marker_idx is not None and marker_idx + 1 < len(args):
            bare = args[marker_idx + 1]
            if bare.lower() not in _STOP_WORDS:
                create_bare_path = bare

    if create_bare_path and is_create_file and "." not in create_bare_path:
        lang_ext = extension_from_prompt(args)
        if lang_ext:
            create_bare_path = f"{create_bare_path}{lang_ext}"
        else:
            chosen_ext = _pick_extension_auto(context, console)
            if chosen_ext is None:
                print("Cancelled.")
                return None
            create_bare_path = f"{create_bare_path}.{chosen_ext}"

    if create_bare_path and not new_file:
        stem, ext = os.path.splitext(create_bare_path)
        new_file = (stem, ext)
        filename = create_bare_path

    if new_file and filename is None:
        raw_name, extension = new_file
        formats = format_filename(raw_name, extension)
        label_str = "format" if not extension else f"{extension} format"
        print(f"\nWhat filename format do you want?\n")
        for i, fmt in enumerate(formats, 1):
            styles = ["snake_case", "kebab-case", "camelCase"]
            print(f"  {i}. {fmt}  ({styles[i-1]})")
        if console.yes or console.dry_run:
            filename = formats[0]
            prefix = "[dry-run] " if console.dry_run else ""
            print(f"\n{prefix}Auto-selected filename: {filename}")
        else:
            answer = console.ask_input(
                f"\nSelect {label_str} [1-3], type a name manually, or Enter to cancel: "
            )
            if not answer:
                print("Cancelled.")
                return None
            elif answer in ("1", "2", "3"):
                filename = formats[int(answer) - 1]
            else:
                manual = answer
                if "." in manual:
                    filename = manual
                elif extension:
                    filename = manual + extension
                else:
                    chosen_ext = _pick_extension(context, console)
                    if chosen_ext is None:
                        print("Cancelled.")
                        return None
                    filename = manual + "." + chosen_ext

    prompt = " ".join(args)
    cmd = llm.ask(prompt, context, None, destination, filename)
    if not cmd:
        return None

    cmd = normalize_template_verb(cmd)

    if "&&" in cmd:
        segments = [s.strip() for s in cmd.split("&&")]
        non_mkdir = [s for s in segments if not s.lstrip().startswith("mkdir")]
        if non_mkdir:
            cmd = " && ".join(non_mkdir)

    if create_bare_path and (is_create_file or is_create_folder):
        dest_prefix = destination.rstrip("/") if destination and destination not in (".", "./") else "."
        target = f"{dest_prefix}/{create_bare_path}"
        verb = "touch" if is_create_file else "mkdir -p"
        cmd = f"{verb} {target}"
    elif filename and new_file:
        raw_name, _ = new_file
        create_dest = destination if (is_create_file or is_create_folder) else None
        cmd = apply_filename(cmd, raw_name, filename, create_dest)

    if create_destination and is_create_file:
        cmd = f"mkdir -p {destination} && {cmd}"

    return cmd
