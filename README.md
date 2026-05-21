# Mash

A bash command agent that lives in your terminal. Designed for people who are not comfortable with bash commands — type what you want to do in plain English and Mash figures out the rest.

```
mash create a new file called bob
```

---

## How it works

**1. Local LLM via Ollama**

Mash uses a local LLM (currently `qwen2.5-coder:7b`) to understand what you want to do. No internet connection required, no API tokens consumed — everything runs on disk.

**2. Python post-processing**

Since small local models can be unpredictable, the LLM output is passed through Python scripts that enforce consistent, correct bash formatting. This layer also drives interactive menus when Mash needs more information:

```
Where should the new file/folder be created?

  1. /path/to/my/folder  (Current directory)

Select option [1], Enter to cancel, type name for other destination: 1

What file extension?

  1. .md

Select extension [1-1], type one manually (with or without dot), or Enter to cancel: .py
```

**3. Confirmation before execution**

Once Mash has the full picture, it shows you the exact shell command and asks before running anything:

```
Run: touch ./bob.py
[y/N]
```

---

## Why Mash?

Remembering bash syntax is annoying. A tiny local agent with one job — turn plain English into shell commands — is useful for developers who haven't mastered the terminal and beginners who want a guided experience.

**Why not just use Claude Code or GitHub Copilot?**

- **No API costs.** Mash runs entirely on your machine using a local model — no cloud credits consumed, no subscription required.
- **Your files stay private.** Nothing is sent over the network. Your file names, paths, and contents never leave your machine.

---

## Project state

Mash works. It currently requires `ollama serve` to be running in a separate terminal — that will change in a future release. It also runs inside a `.venv` for now.

Not yet implemented: user-selectable model, configurable behaviour (e.g. skip menus / just output the command). These are planned for the final product.
