# Mash Agent

**Status legend:**  ⬜ Not started · 🟡 In progress · ✅ Done

## Problem

Developers waste time looking up exact shell command syntax for things they already know conceptually. There's no quick way to say "find all PDFs modified this week" and get the right command without googling or guessing flags.

## Goal

A local CLI tool that accepts a natural language query, uses a local LLM to classify intent and select a template, and executes the resulting command after user confirmation. Python constructs the actual command — the LLM has no creative latitude. No internet required after initial model download.

## Project parts

| Part | Details |
|------|---------|
| **Interface** | CLI (`mash <natural language>`) |
| **Backend** | None |
| **Database** | None |
| **External APIs** | None |
| **Auth** | None |
| **Hosting** | Local only |
| **ML / AI** | Yes — Ollama local server, qwen2.5-coder:7b |

---

## Phase goals

| Phase | Goal | Deliverable |
|-------|------|-------------|
| **Phase 0** | Setup | Ollama installed and model running locally |
| **Phase 1** | Core agent | `mash` command installed, file-aware, template-driven |
| **Phase 2** | Stress test + bug fixes → MVP | Headless test suite run and surfaced bugs fixed; usable MVP |
| **Phase 3** | User selection menus + source/destination path bugs | Well-working MVP within a selected directory |

---

## Phase 0 — Setup

**Goal:** Ollama installed, model pulled, server running. No code written yet.

| # | Step | Plan | Status |
|---|------|------|--------|
| 0.1 | Install Ollama | — | ✅ |
| 0.2 | Pull qwen2.5-coder:7b model | — | ✅ |
| 0.3 | Confirm `ollama serve` runs in background | — | ✅ |

---

## Phase 1 — Core Agent

**Goal:** `mash <query>` installed as a CLI command, classifies intent via LLM, selects a template, constructs the command in Python, shows a run confirmation, and executes — with directory context and hardcoded templates.

| # | Step | Plan | Status |
|---|------|------|--------|
| 1.0 | Core agent: package, `ask_llm`, `confirm_and_run`, `run` | [1.0_core_agent.md](implementation_plans/1.0_core_agent.md) | ✅ |
| 1.1 | File-aware directory context in LLM prompt | [1.1_file_aware_context.md](implementation_plans/1.1_file_aware_context.md) | ✅ |
| 1.2 | Command templates + Python file resolver | [1.2_command_templates.md](implementation_plans/1.2_command_templates.md) | ✅ |

---

## Phase 2 — Stress test + bug fixes (MVP)

**Goal:** Run a headless stress test of `mash` and fix the issues it surfaces — leaving an MVP that handles the core flow end-to-end.

| # | Step | Plan | Status |
|---|------|------|--------|
| 2.1 | Mash headless stress test | [2.1_stress_test.md](test_plans/2.1_stress_test.md) | ✅ |
| 2.3 | Fix resolver false matches, disambiguation menus, wrong destination | [2.3_bug_fixes.md](implementation_plans/2.3_bug_fixes.md) | ✅ |

---

## Phase 3 — User selection menus + source/destination path bugs

**Goal:** A well-working MVP within a selected directory — disambiguation menus behave correctly and source/destination path resolution is reliable.

| # | Step | Plan | Status |
|---|------|------|--------|
| 3.0 | Verification test plan for 2.3 bug fixes | [3.0_test_plan.md](test_plans/3.0_test_plan.md) | ⬜ |
| 3.1 | Fixes for bugs found in verification run (V1–V4) | [3.1_bugs_found_and_fixes.md](implementation_plans/3.1_bugs_found_and_fixes.md) | ✅ |
| 3.2 | Source selection menu doesn't fire for short filenames | [3.2_source_selection_bug.md](implementation_plans/3.2_source_selection_bug.md) | ✅ |
| 3.3 | Shallowest path as default candidate | [3.3_shallow_to_default.md](implementation_plans/3.3_shallow_to_default.md) | ✅ |
| 3.4 | Improved disambiguation menus (type-to-retry, single-match confirm, manual filename) | [3.4_improved_menus.md](implementation_plans/3.4_improved_menus.md) | ✅ |
| 3.5 | Destination not-found menu + rename intent + file/folder-aware templates + blank-cancel fix (Bugs 7, 1, 2 & 6) | [3.5_bug_fix.md](implementation_plans/3.5_bug_fix.md) | ✅ |
| 3.6 | Mandatory destination confirmation for create-file / create-folder (Bug 9) | [3.6_touch_bug_fix.md](implementation_plans/3.6_touch_bug_fix.md) | ✅ |
| 3.7 | Rename must preserve file extension unless explicitly changed (Bug 10) | [3.7_rename_extension_bug.md](implementation_plans/3.7_rename_extension_bug.md) | ✅ |
| 3.8 | Align all interactive prompts with unified UX from mash_behavior.md | [3.8_mash_behaviour_update.md](implementation_plans/3.8_mash_behaviour_update.md) | ✅ |
| 3.9 | New list/open/cat flows + create-without-marker fix | [3.9_mash_behaviour_update.md](implementation_plans/3.9_mash_behaviour_update.md) | ✅ |
| 3.10 | List-flow fixes + move/copy missing-destination + bare-name extension | [3.10_mash_behavior_update.md](implementation_plans/3.10_mash_behavior_update.md) | ✅ |
| 3.11 | Bug fixes confirmed from Test Plan 3.0 run | [3.11_bug_fixes.md](implementation_plans/3.11_bug_fixes.md) | ✅ |

---

## Phase 4 — OOP Refactor

**Goal:** Restructure `mash/main.py` into focused modules with three core classes: `Intent`, `Console`, and `LLMClient`. Behaviour must be identical after the rewrite.

| # | Step | Plan | Status |
|---|------|------|--------|
| 4.0 | OOP refactor: Intent, Console, LLMClient modules | [4.0_oop_refactor.md](implementation_plans/4.0_oop_refactor.md) | ⬜ |

---

## Open decisions & pre-launch requirements

| # | Item | Decision | Resolved |
|---|------|----------|----------|
| D1 | Should `--yes` / auto-run flag ever be added? | Implemented as a development-only testing aid for Claude. Not user-facing. May be removed if unhelpful for testing. | ✅ |
| D2 | Custom model selection at runtime (`--model`) | Hardcoded to `qwen2.5-coder:7b` for now. User-selectable model configuration planned as a pre-ship feature. | ✅ |
| D3 | Multi-step / chained command support | Permanently out of scope. Mash handles one action per invocation. | ✅ |
