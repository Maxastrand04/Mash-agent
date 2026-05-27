import pytest
import sys
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def capture_cli(argv):
    sys.path.insert(0, str(PROJECT_ROOT))
    from mash.mash_cli import MashCLI
    output = StringIO()
    with patch("sys.argv", argv):
        with redirect_stdout(output):
            try:
                MashCLI().run()
            except SystemExit:
                pass
    return output.getvalue()


def test_cancel_at_source_picker(test_tree, monkeypatch):
    monkeypatch.chdir(test_tree)
    with patch("mash.helpers.selection.source_selector.SourceSelector.select") as mock_sel:
        from mash.exceptions import UserCancelled
        mock_sel.side_effect = UserCancelled()
        out = capture_cli(["mash", "delete", "foo"])
    assert "Cancelled." in out
    assert "Traceback" not in out


def test_cancel_at_destination_picker(test_tree, monkeypatch):
    monkeypatch.chdir(test_tree)
    with patch("mash.helpers.selection.source_selector.SourceSelector.select") as src_sel:
        src_sel.return_value = "./archive/notes.txt"
        with patch("mash.helpers.selection.destination_selector.DestinationSelector.select") as dst_sel:
            from mash.exceptions import UserCancelled
            dst_sel.side_effect = UserCancelled()
            out = capture_cli(["mash", "move", "notes", "to", "reports"])
    assert "Cancelled." in out
    assert "Traceback" not in out


def test_cancel_at_extension_picker(test_tree, monkeypatch):
    monkeypatch.chdir(test_tree)
    from mash.exceptions import UserCancelled
    with patch("mash.helpers.selection.destination_selector.DestinationSelector.select") as dst_sel:
        dst_sel.return_value = (".", False)
        with patch("mash.helpers.selection.create_kind_picker.CreateKindPicker.pick") as kind_sel:
            kind_sel.return_value = "file"
            with patch("mash.helpers.selection.extension_picker.ExtensionPicker.pick") as ext_sel:
                ext_sel.side_effect = UserCancelled()
                out = capture_cli(["mash", "create", "something"])
    assert "Cancelled." in out
    assert "Traceback" not in out


def test_cancel_at_run_confirm(test_tree, monkeypatch):
    monkeypatch.chdir(test_tree)
    with patch("mash.helpers.console.Console.confirm_and_run") as mock_confirm:
        mock_confirm.return_value = None
        with patch("mash.mash_cli.DirectoryContext") as mock_dc:
            mock_dc.get.return_value = ".\narchive\narchive/notes.txt"
            with patch("sys.argv", ["mash", "delete", "notes"]):
                from mash.exceptions import UserCancelled
                with patch("mash.helpers.selection.source_selector.SourceSelector.select") as src:
                    src.side_effect = UserCancelled()
                    from mash.mash_cli import MashCLI
                    output = StringIO()
                    with redirect_stdout(output):
                        MashCLI().run()
    out = output.getvalue()
    assert "Traceback" not in out
