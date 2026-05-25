import ollama
from mash.helpers.commands import COMMANDS_LIST, TEMPLATES_LIST


class LLMError(Exception):
    """Raised when the underlying ollama.chat call fails.

    Wraps the original exception via `raise … from e` so callers can
    catch a single type without depending on ollama internals.
    """
    pass


class LLMClient:
    """Wrapper around a local ollama model for command generation.

    Encapsulates the SYSTEM_PROMPT so flows only have to pass user-level
    inputs, and centralizes prompt construction so resolved paths reach
    the model in a uniform schema.
    """

    SYSTEM_PROMPT = (
        "You are a bash command generator. "
        "Output only a single bash command with no explanation, "
        "no markdown formatting, and no extra text.\n\n"
        f"Available command templates:\n{TEMPLATES_LIST}\n\n"
        f"Available shell commands:\n{COMMANDS_LIST}\n\n"
        "Follow these rules strictly:\n"
        "0. Use the command templates above. Each entry is 'intent_label: bash_command_template'. "
        "Pick the entry whose intent matches the user's request, substitute the placeholders with "
        "actual paths, and output ONLY the resulting bash command (e.g. 'mv ./foo.pdf ./bar/'). "
        "NEVER output the intent label (e.g. never output 'move_file', 'copy_folder', etc.).\n"
        "1. File paths are resolved for you and provided as 'Resolved path: <path>', "
        "'Resolved destination: <path>', 'Resolved filename: <name>', and/or 'Resolved after: <name>'. "
        "Use them exactly as given — do not modify or guess them.\n"
        "2. Never invent a path that was not resolved for you. "
        "If no resolved path is provided, use the directory tree.\n"
        "3. Never go above the current directory (no '..' in paths).\n"
        "4. If no match is found in the tree, generate the most reasonable command you can.\n"
        "5. When moving or copying a file INTO a directory, use the directory path as the "
        "destination (e.g. 'mv ./file.txt ./reports/'). If a 'Resolved destination' is provided, "
        "use it exactly — never a file that already exists inside that directory.\n"
        "6. Source type: when 'Source type: file' is provided, use delete_file (rm), "
        "copy_file (cp), and move_file (mv). When 'Source type: directory', use "
        "delete_folder (rm -rf), copy_folder (cp -r), and move_folder (mv). "
        "When no source type is provided, prefer file-safe variants (rm and cp — no -rf or -r flags).\n"
        "7. Rename: when 'Resolved after: <name>' is provided, use the rename template "
        "(mv {before} {after}). 'Resolved path' is {before} and 'Resolved after' is {after}. "
        "If 'Resolved destination' is also provided, combine them: mv {before} {destination}/{after}.\n"
        "8b. Copy synonyms: treat 'duplicate', 'clone', and 'replicate' as copy intents — "
        "pick copy_file or copy_folder (cp / cp -r) just like 'copy'.\n"
        "8. Create intents: for 'create a file …' pick create_file (touch {path}); for "
        "'create a directory/folder …' pick create_folder (mkdir -p {path}). "
        "When a 'Resolved destination' is provided, prefix {path} with it "
        "(e.g. touch ./sandbox/foo.py, mkdir -p ./sandbox/newdir). "
        "The post-processor enforces this even if you omit the prefix.\n"
    )

    def __init__(self, model: str = "qwen2.5-coder:7b"):
        """Bind the client to a specific ollama model.

        Args:
            model: ollama model tag to send requests to.

        Returns:
            None.

        Raises:
            None.
        """
        self.model = model

    def ask(
        self,
        prompt: str,
        context: str,
        resolved: str | None,
        destination: str | None,
        filename: str | None,
        source_type: str | None = None,
        after: str | None = None,
    ) -> str:
        """Send a single chat-completion request and return the bash command.

        Resolved paths are injected into the user message as labelled lines
        so the model can quote them verbatim — the SYSTEM_PROMPT forbids
        modifying them, and the downstream sanitizers force-apply them
        even if the model deviates.

        Args:
            prompt: Raw natural-language request from the user.
            context: Directory tree string from get_directory_context.
            resolved: User-disambiguated source path, if any.
            destination: User-disambiguated destination directory, if any.
            filename: Final filename for create flows, if any.
            source_type: "file", "directory", or "unknown" — drives the
                file-vs-folder template choice on the LLM side.
            after: Target name for rename flows.

        Returns:
            The model's response stripped of surrounding whitespace.

        Raises:
            LLMError: Wrapped failure from ollama.chat.
        """
        extra = ""
        if resolved:
            extra += f"\nResolved path: {resolved}"
        if source_type and source_type != "unknown":
            extra += f"\nSource type: {source_type}"
        if destination and destination not in (".", "./"):
            extra += f"\nResolved destination: {destination}"
        if after:
            extra += f"\nResolved after: {after}"
        if filename:
            extra += f"\nResolved filename: {filename}"
        full_prompt = (
            f"Current directory tree:\n{context}"
            f"{extra}\n\n"
            f"User request: {prompt}"
        )
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt},
                ],
            )
        except Exception as e:
            raise LLMError("ollama.chat failed") from e
        # Strip trailing/leading whitespace and newlines so downstream command parsing sees a clean bash command.
        return response.message.content.strip()
