# Comment Convention

## Global rules

- Comments explain *why*, not *what*. Code already shows what it does.
- Exceptions where descriptive WHAT is allowed: regex patterns, non-obvious algorithms, public-API docstrings.

---

## Python

- **Style**: above-symbol only (docstring placed immediately after `def`/`class`). No inline `#` comments except rare local-variable exceptions.
- **Format**: Google-style docstrings (`Args:` / `Returns:` / `Raises:`).
- **Params**: all functions document every parameter.
- **Returns**: always documented (including `None`).
- **Exceptions**: every function that raises documents it via `Raises:`.
- **Local variables**: inline `# WHY` only when the assignment is non-obvious.
- **Idiom**: always multi-line — summary line, blank line, then `Args` / `Returns` / `Raises` sections, even for trivial functions.
