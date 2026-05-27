import os
from mash.helpers.files import Extensions, PathResolver
from mash.helpers.commands import CommandSanitizer
from mash.intent import Intent
from mash.exceptions import UserCancelled, DestinationNotFound, InvalidExtension, LLMUnavailable


class CreateFlow:
    def __init__(self, console, llm_client, destination_selector, create_kind_picker, extension_picker, directory_context: str):
        self.console = console
        self.llm_client = llm_client
        self.destination_selector = destination_selector
        self.create_kind_picker = create_kind_picker
        self.extension_picker = extension_picker
        self.directory_context = directory_context

    def run(self, intent) -> str | None:
        try:
            return self._run(intent)
        except (UserCancelled, DestinationNotFound):
            self.console.print_info("Cancelled.")
            return None
        except InvalidExtension:
            self.console.print_info("Cancelled.")
            return None

    def _run(self, intent) -> str | None:
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
                if i != 0 and i != dest_idx_val and w.lower() not in Intent._STOP_WORDS
            ]
            if candidate_tokens:
                choice = self.create_kind_picker.pick()
                if choice == "file":
                    is_create_file = True
                    create_bare_path = candidate_tokens[0][1]
                else:
                    is_create_folder = True
                    create_bare_path = candidate_tokens[0][1]

        dest_candidates = PathResolver.resolve_dirs(self.directory_context, dest_token) if dest_token is not None else []
        destination, create_destination = self.destination_selector.select(
            dest_candidates,
            self.directory_context,
            destination_token=dest_token,
            for_create=True,
        )

        filename: str | None = None
        new_file = Intent._detect_new_filename(args)

        if is_create_file and not create_bare_path and not new_file:
            markers = {"called", "named"}
            marker_idx = next((i for i, w in enumerate(args) if w.lower() in markers), None)
            if marker_idx is not None and marker_idx + 1 < len(args):
                bare = args[marker_idx + 1]
                if bare.lower() not in Intent._STOP_WORDS:
                    create_bare_path = bare

        if create_bare_path and is_create_file and "." not in create_bare_path:
            lang_ext = Extensions.from_prompt(args)
            if lang_ext:
                create_bare_path = f"{create_bare_path}{lang_ext}"
            else:
                chosen_ext = self.extension_picker.pick(self.directory_context)
                create_bare_path = f"{create_bare_path}.{chosen_ext}"

        if create_bare_path and not new_file:
            stem, extension = os.path.splitext(create_bare_path)
            new_file = (stem, extension)
            filename = create_bare_path

        if new_file and filename is None:
            raw_name, extension = new_file
            formats = Extensions.format_filename(raw_name, extension)
            print(f"\nWhat filename format do you want?\n")
            for i, fmt in enumerate(formats, 1):
                styles = ["snake_case", "kebab-case", "camelCase"]
                print(f"  {i}. {fmt}  ({styles[i-1]})")
            if self.console.yes or self.console.dry_run:
                filename = formats[0]
                prefix = "[dry-run] " if self.console.dry_run else ""
                print(f"\n{prefix}Auto-selected filename: {filename}")
            else:
                label_str = "format" if not extension else f"{extension} format"
                answer = self.console.ask_input(
                    f"\nSelect {label_str} [1-3], type a name manually, or Enter to cancel: "
                )
                if not answer:
                    raise UserCancelled
                elif answer in ("1", "2", "3"):
                    filename = formats[int(answer) - 1]
                else:
                    manual = answer
                    if "." in manual:
                        filename = manual
                    elif extension:
                        filename = manual + extension
                    else:
                        chosen_ext = self.extension_picker.pick(self.directory_context)
                        filename = manual + "." + chosen_ext

        prompt = " ".join(args)
        command = self.llm_client.ask(prompt, self.directory_context, None, destination, filename)
        if not command:
            raise LLMUnavailable("LLM returned empty response")

        command = CommandSanitizer.normalize_template_verb(command)

        if "&&" in command:
            segments = [s.strip() for s in command.split("&&")]
            non_mkdir = [s for s in segments if not s.lstrip().startswith("mkdir")]
            if non_mkdir:
                command = " && ".join(non_mkdir)

        if create_bare_path and (is_create_file or is_create_folder):
            dest_prefix = destination.rstrip("/") if destination and destination not in (".", "./") else "."
            target = f"{dest_prefix}/{create_bare_path}"
            verb = "touch" if is_create_file else "mkdir -p"
            command = f"{verb} {target}"
        elif filename and new_file:
            raw_name, _ = new_file
            create_dest = destination if (is_create_file or is_create_folder) else None
            command = CommandSanitizer.apply_filename(command, raw_name, filename, create_dest)

        if create_destination and is_create_file:
            command = f"mkdir -p {destination} && {command}"

        return command
