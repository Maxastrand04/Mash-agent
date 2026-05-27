import pytest
from mash.helpers.files.extensions import Extensions


def test_from_prompt_hit():
    assert Extensions.from_prompt(["create", "python", "file"]) == ".py"


def test_from_prompt_short_alias():
    assert Extensions.from_prompt(["create", "py", "file"]) == ".py"


def test_from_prompt_miss():
    assert Extensions.from_prompt(["create", "thing"]) is None


def test_from_prompt_empty():
    assert Extensions.from_prompt([]) is None


def test_collect_orders_by_frequency():
    ctx = "a.py\nb.py\nc.md\nd.py\ne.md\nf.txt"
    out = Extensions.collect(ctx)
    assert out[0] == "py"
    assert "md" in out
    assert "txt" in out


def test_collect_ignores_lines_without_suffix():
    ctx = "dir1\ndir2\nfile.py"
    assert Extensions.collect(ctx) == ["py"]


def test_collect_empty_context():
    assert Extensions.collect("") == []


def test_collect_only_dirs():
    assert Extensions.collect("src\ndocs\nbuild") == []


def test_format_filename_returns_snake_kebab_camel():
    out = Extensions.format_filename("My Cool Report", ".md")
    assert out == ["my_cool_report.md", "my-cool-report.md", "myCoolReport.md"]


def test_format_filename_single_word():
    out = Extensions.format_filename("report", ".txt")
    assert "report.txt" in out


def test_reconcile_after_missing_extension_uses_before():
    name, flag = Extensions.reconcile_rename("foo.txt", "bar")
    assert name == "bar.txt"
    assert flag is None


def test_reconcile_same_extension_no_flag():
    name, flag = Extensions.reconcile_rename("foo.txt", "bar.txt")
    assert name == "bar.txt"
    assert flag is None


def test_reconcile_different_extension_flag():
    name, flag = Extensions.reconcile_rename("foo.txt", "bar.md")
    assert name == "bar.md"
    assert flag == "different_extension"


def test_reconcile_no_extensions_either_side():
    name, flag = Extensions.reconcile_rename("foo", "bar")
    assert name == "bar"
    assert flag is None


def test_reconcile_adds_extension_when_only_after_has_one():
    name, flag = Extensions.reconcile_rename("foo", "bar.py")
    assert name == "bar.py"
    assert flag == "add_extension"


def test_extension_map_is_class_attribute():
    assert isinstance(Extensions.EXTENSION_MAP, dict)
    assert Extensions.EXTENSION_MAP["py"] == ".py"
    assert Extensions.EXTENSION_MAP["markdown"] == ".md"
