import pytest
import os
from unittest.mock import patch
from mash.flows.list_scope import ListScope


FAKE_CONTEXT = ".\nreports\narchive\nfoo.txt"


def test_list_entries_returns_tuples(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()
    entries = ListScope.list_entries(str(tmp_path))
    paths = [e[0] for e in entries]
    is_dirs = [e[1] for e in entries]
    assert any("a.txt" in p for p in paths)
    assert any(d for d in is_dirs)


def test_list_entries_ignores_hidden(tmp_path):
    (tmp_path / ".hidden").write_text("")
    (tmp_path / "visible.txt").write_text("")
    entries = ListScope.list_entries(str(tmp_path))
    names = [os.path.basename(e[0]) for e in entries]
    assert ".hidden" not in names
    assert "visible.txt" in names


def test_list_entries_invalid_path_returns_empty():
    entries = ListScope.list_entries("/nonexistent/path/xyz")
    assert entries == []


def test_scope_label_cwd_returns_dot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    label = ListScope.scope_label(str(tmp_path))
    assert label == "."


def test_scope_label_relative_returns_relative(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subdir = tmp_path / "reports"
    subdir.mkdir()
    label = ListScope.scope_label(str(subdir))
    assert "reports" in label


def test_list_target_from_arguments_returns_dot_when_no_match():
    result = ListScope.list_target_from_arguments(["list"], FAKE_CONTEXT)
    assert result == "."


def test_list_target_from_arguments_marker_in():
    result = ListScope.list_target_from_arguments(
        ["list", "in", "reports"], ".\nreports\nfoo.txt"
    )
    assert "reports" in result


def test_list_target_from_arguments_no_marker():
    result = ListScope.list_target_from_arguments(
        ["list", "reports"], ".\nreports\nfoo.txt"
    )
    assert "reports" in result


def test_scoped_context_returns_string(tmp_path):
    (tmp_path / "file.txt").write_text("hello")
    result = ListScope.scoped_context(str(tmp_path))
    assert isinstance(result, str)


def test_scope_label_outside_cwd_returns_abs_path(tmp_path, monkeypatch):
    subdir = tmp_path / "work"
    subdir.mkdir()
    monkeypatch.chdir(subdir)
    result = ListScope.scope_label(str(tmp_path))
    assert result == str(tmp_path)


def test_list_target_from_arguments_marker_with_no_match_then_fallback():
    result = ListScope.list_target_from_arguments(
        ["list", "in", "nonexistent", "reports"], ".\nreports\nfoo.txt"
    )
    assert "reports" in result


def test_list_target_from_arguments_non_stop_word_no_dir_match():
    result = ListScope.list_target_from_arguments(
        ["move", "zzznomatch", "reports"], ".\nreports\nfoo.txt"
    )
    assert "reports" in result
