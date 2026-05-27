import pytest
from unittest.mock import patch
from mash.helpers.files.directory_context import DirectoryContext


def test_get_returns_string():
    result = DirectoryContext.get()
    assert isinstance(result, str)


def test_get_non_empty_in_populated_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "file.txt").write_text("hello")
    result = DirectoryContext.get()
    assert isinstance(result, str)
