from mash.helpers.files.resolver import resolve_paths, resolve_dirs


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
    out = resolve_paths(TREE, "main")
    assert "src/main.py" in out


def test_resolve_paths_no_match_returns_empty():
    out = resolve_paths(TREE, "zzznomatch")
    assert out == []


def test_resolve_paths_sorted_by_depth():
    tree = "foo.py\nsub/foo.py\nsub/deep/foo.py"
    out = resolve_paths(tree, "foo")
    assert out == ["foo.py", "sub/foo.py", "sub/deep/foo.py"]


def test_resolve_dirs_excludes_files_with_extension():
    out = resolve_dirs(TREE, "main")
    assert "src/main.py" not in out


def test_resolve_dirs_excludes_dot():
    out = resolve_dirs(TREE, ".")
    assert "." not in out


def test_resolve_dirs_close_match_returns_dir_only():
    out = resolve_dirs(TREE, "helpers")
    assert "src/helpers" in out
    assert all(not p.endswith(".py") for p in out)
