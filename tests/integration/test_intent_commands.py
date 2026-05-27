import subprocess
import sys
import os
from pathlib import Path

import pytest

GOLDEN_DIR = Path(__file__).parent / "golden"
PROJECT_ROOT = Path(__file__).parent.parent.parent
MASH_BIN = PROJECT_ROOT / ".venv" / "bin" / "mash"


def run_mash(args, cwd):
    result = subprocess.run(
        [str(MASH_BIN)] + args,
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    return result.stdout


def test_list(test_tree):
    out = run_mash(["--dry-run", "--yes", "list"], cwd=test_tree)
    golden = (GOLDEN_DIR / "list.txt").read_text()
    assert out == golden


def test_cat(test_tree):
    out = run_mash(["--dry-run", "--yes", "cat", "overview"], cwd=test_tree)
    golden = (GOLDEN_DIR / "cat.txt").read_text()
    assert out == golden


def test_open(test_tree):
    out = run_mash(["--dry-run", "--yes", "open", "summary"], cwd=test_tree)
    golden = (GOLDEN_DIR / "open.txt").read_text()
    assert out == golden


def test_delete_file(test_tree):
    from unittest.mock import patch, MagicMock
    import sys

    sys.path.insert(0, str(PROJECT_ROOT))
    os.chdir(str(test_tree))

    mock_response = MagicMock()
    mock_response.message.content = "rm ./archive/notes.txt"

    with patch("ollama.chat", return_value=mock_response):
        with patch("sys.argv", ["mash", "--dry-run", "--yes", "delete", "notes"]):
            from mash.mash_cli import MashCLI
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                MashCLI().run()
            out = f.getvalue()

    golden = (GOLDEN_DIR / "delete_file.txt").read_text()
    assert out == golden


def test_delete_folder(test_tree):
    import sys
    from unittest.mock import patch, MagicMock

    sys.path.insert(0, str(PROJECT_ROOT))
    os.chdir(str(test_tree))

    mock_response = MagicMock()
    mock_response.message.content = "rm -rf ./reports"

    with patch("ollama.chat", return_value=mock_response):
        with patch("sys.argv", ["mash", "--dry-run", "--yes", "delete", "reports"]):
            from mash.mash_cli import MashCLI
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                MashCLI().run()
            out = f.getvalue()

    golden = (GOLDEN_DIR / "delete_folder.txt").read_text()
    assert out == golden


def test_create_folder(test_tree):
    import sys
    from unittest.mock import patch, MagicMock

    sys.path.insert(0, str(PROJECT_ROOT))
    os.chdir(str(test_tree))

    mock_response = MagicMock()
    mock_response.message.content = "mkdir -p ./exports"

    with patch("ollama.chat", return_value=mock_response):
        with patch("sys.argv", ["mash", "--dry-run", "--yes", "create", "folder", "exports"]):
            from mash.mash_cli import MashCLI
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                MashCLI().run()
            out = f.getvalue()

    golden = (GOLDEN_DIR / "create_folder.txt").read_text()
    assert out == golden
