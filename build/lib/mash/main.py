import sys
import subprocess
import ollama

MODEL = "qwen2.5-coder:7b"
SYSTEM_PROMPT = (
    "You are a bash command generator. "
    "Output only a single bash command with no explanation, "
    "no markdown formatting, and no extra text."
)


def ask_llm(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.message.content.strip()


def confirm_and_run(cmd: str) -> None:
    print(f"Run: {cmd}")
    answer = input("[y/N] ").strip().lower()
    if answer == "y":
        subprocess.run(cmd, shell=True)
    else:
        print("Cancelled.")


def run() -> None:
    if len(sys.argv) < 2:
        print("Usage: mash <what you want to do>")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    cmd = ask_llm(prompt)

    if not cmd:
        print("No command generated.")
        sys.exit(1)

    confirm_and_run(cmd)
