import pytest
import sys
from unittest.mock import patch, MagicMock
from mash.mash_cli import MashCLI
from mash.exceptions import LLMUnavailable, MashError


def run_cli(args, monkeypatch_fn=None):
    with patch("sys.argv", ["mash"] + args):
        cli = MashCLI()
        cli.run()


def test_no_args_prints_usage_and_exits(capsys):
    with patch("sys.argv", ["mash"]):
        with pytest.raises(SystemExit):
            MashCLI().run()
    out = capsys.readouterr().out
    assert "Usage:" in out


def test_main_classmethod_exists():
    assert callable(MashCLI.main)


def test_yes_flag_parsed():
    cli = MashCLI()
    cli._yes = False
    cli._dry_run = False
    with patch("sys.argv", ["mash", "--yes", "list"]):
        with patch.object(cli, "_run_with_args") as mock_run:
            cli.run()
            assert cli._yes is True


def test_dry_run_flag_parsed():
    cli = MashCLI()
    with patch("sys.argv", ["mash", "--dry-run", "list"]):
        with patch.object(cli, "_run_with_args") as mock_run:
            cli.run()
            assert cli._dry_run is True


def test_llm_unavailable_prints_message_and_exits(capsys):
    cli = MashCLI()
    cli._yes = True
    cli._dry_run = True
    with patch("sys.argv", ["mash", "--yes", "--dry-run", "move", "foo", "to", "bar"]):
        with patch("mash.mash_cli.DirectoryContext") as mock_dc:
            mock_dc.get.return_value = "."
            with patch("mash.mash_cli.MoveCopyFlow") as mock_flow_cls:
                mock_flow = MagicMock()
                mock_flow.run.side_effect = LLMUnavailable("fail")
                mock_flow_cls.return_value = mock_flow
                with pytest.raises(SystemExit) as exc_info:
                    cli.run()
                assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "LLM not working" in out


def test_mash_error_prints_message_and_exits(capsys):
    cli = MashCLI()
    with patch("sys.argv", ["mash", "--yes", "--dry-run", "move", "foo", "to", "bar"]):
        with patch("mash.mash_cli.DirectoryContext") as mock_dc:
            mock_dc.get.return_value = "."
            with patch("mash.mash_cli.MoveCopyFlow") as mock_flow_cls:
                mock_flow = MagicMock()
                mock_flow.run.side_effect = MashError("something broke")
                mock_flow_cls.return_value = mock_flow
                with pytest.raises(SystemExit) as exc_info:
                    cli.run()
                assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "mash:" in out


def test_short_yes_flag():
    cli = MashCLI()
    with patch("sys.argv", ["mash", "-y", "list"]):
        with patch.object(cli, "_run_with_args"):
            cli.run()
            assert cli._yes is True


def test_main_calls_run():
    with patch.object(MashCLI, "run") as mock_run:
        with patch("sys.argv", ["mash", "list"]):
            MashCLI.main()
            mock_run.assert_called_once()


def test_run_with_args_open_verb(capsys):
    with patch("sys.argv", ["mash", "--yes", "--dry-run", "open", "foo"]):
        with patch("mash.mash_cli.DirectoryContext") as mock_dc:
            mock_dc.get.return_value = "."
            with patch("mash.mash_cli.OpenCatFlow") as mock_flow_cls:
                mock_flow = MagicMock()
                mock_flow.run.return_value = "open ./foo.txt"
                mock_flow_cls.return_value = mock_flow
                with patch("mash.mash_cli.Console") as mock_console_cls:
                    mock_console = MagicMock()
                    mock_console_cls.return_value = mock_console
                    MashCLI().run()
                    mock_console.confirm_and_run.assert_called_once_with("open ./foo.txt")


def test_run_with_args_open_verb_returns_none(capsys):
    with patch("sys.argv", ["mash", "--yes", "open", "foo"]):
        with patch("mash.mash_cli.DirectoryContext") as mock_dc:
            mock_dc.get.return_value = "."
            with patch("mash.mash_cli.OpenCatFlow") as mock_flow_cls:
                mock_flow = MagicMock()
                mock_flow.run.return_value = None
                mock_flow_cls.return_value = mock_flow
                MashCLI().run()


def test_run_with_args_list_verb():
    with patch("sys.argv", ["mash", "--yes", "--dry-run", "list"]):
        with patch("mash.mash_cli.DirectoryContext") as mock_dc:
            mock_dc.get.return_value = "."
            with patch("mash.mash_cli.ListFlow") as mock_flow_cls:
                mock_flow = MagicMock()
                mock_flow_cls.return_value = mock_flow
                MashCLI().run()
                mock_flow.run.assert_called_once()


def test_run_with_args_rename_verb():
    with patch("sys.argv", ["mash", "--yes", "--dry-run", "rename", "foo", "to", "bar"]):
        with patch("mash.mash_cli.DirectoryContext") as mock_dc:
            mock_dc.get.return_value = "."
            with patch("mash.mash_cli.RenameFlow") as mock_flow_cls:
                mock_flow = MagicMock()
                mock_flow.run.return_value = "mv ./foo ./bar"
                mock_flow_cls.return_value = mock_flow
                with patch("mash.mash_cli.Console") as mock_console_cls:
                    mock_console = MagicMock()
                    mock_console_cls.return_value = mock_console
                    MashCLI().run()
                    mock_console.confirm_and_run.assert_called_once()


def test_run_with_args_rename_verb_returns_none():
    with patch("sys.argv", ["mash", "--yes", "--dry-run", "rename", "foo", "to", "bar"]):
        with patch("mash.mash_cli.DirectoryContext") as mock_dc:
            mock_dc.get.return_value = "."
            with patch("mash.mash_cli.RenameFlow") as mock_flow_cls:
                mock_flow = MagicMock()
                mock_flow.run.return_value = None
                mock_flow_cls.return_value = mock_flow
                with patch("mash.mash_cli.Console") as mock_console_cls:
                    mock_console = MagicMock()
                    mock_console_cls.return_value = mock_console
                    MashCLI().run()
                    mock_console.confirm_and_run.assert_not_called()


def test_run_with_args_delete_verb():
    with patch("sys.argv", ["mash", "--yes", "--dry-run", "delete", "foo"]):
        with patch("mash.mash_cli.DirectoryContext") as mock_dc:
            mock_dc.get.return_value = "."
            with patch("mash.mash_cli.DeleteFlow") as mock_flow_cls:
                mock_flow = MagicMock()
                mock_flow.run.return_value = ("rm ./foo", "./foo")
                mock_flow_cls.return_value = mock_flow
                with patch("mash.mash_cli.Console") as mock_console_cls:
                    mock_console = MagicMock()
                    mock_console_cls.return_value = mock_console
                    MashCLI().run()
                    mock_console.confirm_and_run.assert_called_once()


def test_run_with_args_create_verb():
    with patch("sys.argv", ["mash", "--yes", "--dry-run", "create", "foo.py"]):
        with patch("mash.mash_cli.DirectoryContext") as mock_dc:
            mock_dc.get.return_value = "."
            with patch("mash.mash_cli.CreateFlow") as mock_flow_cls:
                mock_flow = MagicMock()
                mock_flow.run.return_value = "touch ./foo.py"
                mock_flow_cls.return_value = mock_flow
                with patch("mash.mash_cli.Console") as mock_console_cls:
                    mock_console = MagicMock()
                    mock_console_cls.return_value = mock_console
                    MashCLI().run()
                    mock_console.confirm_and_run.assert_called_once()


def test_run_with_args_move_verb_result_returned():
    with patch("sys.argv", ["mash", "--yes", "--dry-run", "move", "foo", "to", "bar"]):
        with patch("mash.mash_cli.DirectoryContext") as mock_dc:
            mock_dc.get.return_value = "."
            with patch("mash.mash_cli.MoveCopyFlow") as mock_flow_cls:
                mock_flow = MagicMock()
                mock_flow.run.return_value = "mv ./foo ./bar/"
                mock_flow_cls.return_value = mock_flow
                with patch("mash.mash_cli.Console") as mock_console_cls:
                    mock_console = MagicMock()
                    mock_console_cls.return_value = mock_console
                    MashCLI().run()
                    mock_console.confirm_and_run.assert_called_once_with("mv ./foo ./bar/")
