from mash.helpers.files.extension import (
    extension_from_prompt,
    collect_extensions,
    format_filename,
    reconcile_rename_extension,
)


def test_extension_from_prompt_hit():
    assert extension_from_prompt(["create", "python", "file"]) == ".py"


def test_extension_from_prompt_miss():
    assert extension_from_prompt(["create", "thing"]) is None


def test_collect_extensions_orders_by_frequency():
    ctx = "a.py\nb.py\nc.md\nd.py\ne.md\nf.txt"
    out = collect_extensions(ctx)
    assert out[0] == "py"
    assert "md" in out
    assert "txt" in out


def test_collect_extensions_ignores_lines_without_suffix():
    ctx = "dir1\ndir2\nfile.py"
    assert collect_extensions(ctx) == ["py"]


def test_format_filename_returns_snake_kebab_camel():
    out = format_filename("My Cool Report", ".md")
    assert out == ["my_cool_report.md", "my-cool-report.md", "myCoolReport.md"]


def test_reconcile_after_missing_extension_uses_before():
    name, flag = reconcile_rename_extension("foo.txt", "bar")
    assert name == "bar.txt"
    assert flag is None


def test_reconcile_same_extension_no_flag():
    name, flag = reconcile_rename_extension("foo.txt", "bar.txt")
    assert name == "bar.txt"
    assert flag is None


def test_reconcile_different_extension_flag():
    name, flag = reconcile_rename_extension("foo.txt", "bar.md")
    assert name == "bar.md"
    assert flag == "different_extension"


def test_reconcile_no_extensions_either_side():
    name, flag = reconcile_rename_extension("foo", "bar")
    assert name == "bar"
    assert flag is None


def test_reconcile_adds_extension_when_only_after_has_one():
    name, flag = reconcile_rename_extension("foo", "bar.py")
    assert name == "bar.py"
    assert flag == "add_extension"
