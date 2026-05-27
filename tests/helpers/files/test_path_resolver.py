import pytest
from mash.helpers.files.path_resolver import PathResolver


TREE = """\
.
src
src/main.py
src/utils.py
src/helpers
src/helpers/parser.py
docs
docs/readme.md
"""


def test_resolve_paths_close_match():
    out = PathResolver.resolve_paths(TREE, "main")
    assert "src/main.py" in out


def test_resolve_paths_no_match_returns_empty():
    out = PathResolver.resolve_paths(TREE, "zzznomatch")
    assert out == []


def test_resolve_paths_sorted_by_depth():
    tree = "foo.py\nsub/foo.py\nsub/deep/foo.py"
    out = PathResolver.resolve_paths(tree, "foo")
    assert out == ["foo.py", "sub/foo.py", "sub/deep/foo.py"]


def test_resolve_paths_returns_list():
    out = PathResolver.resolve_paths(TREE, "utils")
    assert isinstance(out, list)
    assert "src/utils.py" in out


def test_resolve_dirs_excludes_files_with_extension():
    out = PathResolver.resolve_dirs(TREE, "main")
    assert "src/main.py" not in out


def test_resolve_dirs_excludes_dot():
    out = PathResolver.resolve_dirs(TREE, ".")
    assert "." not in out


def test_resolve_dirs_close_match_returns_dir_only():
    out = PathResolver.resolve_dirs(TREE, "helpers")
    assert "src/helpers" in out
    assert all(not p.endswith(".py") for p in out)


def test_resolve_dirs_no_match_returns_empty():
    out = PathResolver.resolve_dirs(TREE, "zzznomatch")
    assert out == []


def test_resolve_paths_empty_context():
    assert PathResolver.resolve_paths("", "foo") == []


def test_resolve_dirs_empty_context():
    assert PathResolver.resolve_dirs("", "foo") == []


def test_resolve_paths_deduplicates_duplicate_lines():
    context = "reports.txt\nreports.txt\nother.md"
    result = PathResolver.resolve_paths(context, "reports")
    assert result.count("reports.txt") == 1


def test_resolve_dirs_deduplicates_duplicate_lines():
    context = "reports\nreports\narchive"
    result = PathResolver.resolve_dirs(context, "reports")
    assert result.count("reports") == 1
