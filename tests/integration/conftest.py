import os
import pytest


@pytest.fixture
def test_tree(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "overview.md").write_text("")
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "summary.pdf").write_text("")
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive" / "notes.txt").write_text("")
    return tmp_path
