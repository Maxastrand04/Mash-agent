import pytest
from unittest.mock import patch
from mash.helpers.console import Console
from mash.exceptions import UserCancelled


def test_confirm_action_yes_mode_returns_true():
    console = Console(yes=True, dry_run=False)
    assert console.confirm_action("delete", "/x") is True


def test_confirm_action_dry_run_mode_returns_true():
    console = Console(yes=False, dry_run=True)
    assert console.confirm_action("open", "/x") is True


def test_confirm_action_interactive_y_returns_true():
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", return_value="y"):
        assert console.confirm_action("delete", "/x") is True


def test_confirm_action_interactive_n_returns_false():
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", return_value="n"):
        assert console.confirm_action("delete", "/x") is False


def test_confirm_action_interactive_eof_returns_false():
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", side_effect=EOFError):
        assert console.confirm_action("delete", "/x") is False


def test_ask_input_returns_stripped():
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", return_value="  hello  "):
        assert console.ask_input("prompt: ") == "hello"


def test_ask_input_eof_returns_empty():
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", side_effect=EOFError):
        assert console.ask_input("prompt: ") == ""


def test_confirm_yes_no_y_returns_true():
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", return_value="y"):
        assert console.confirm_yes_no("proceed? ") is True


def test_confirm_yes_no_no_returns_false():
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", return_value="n"):
        assert console.confirm_yes_no("proceed? ") is False


def test_confirm_yes_no_eof_returns_false():
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", side_effect=EOFError):
        assert console.confirm_yes_no("proceed? ") is False


def test_render_menu_contains_options():
    console = Console(yes=True, dry_run=False)
    result = console.render_menu("Header", ["opt1", "opt2"], "Footer")
    assert "opt1" in result
    assert "opt2" in result
    assert "Header" in result
    assert "Footer" in result
    assert "1." in result
    assert "2." in result


def test_abs_path_returns_absolute(tmp_path):
    console = Console(yes=True, dry_run=False)
    result = console.abs_path(str(tmp_path))
    assert result == str(tmp_path)


def test_cwd_label_contains_current_directory():
    console = Console(yes=True, dry_run=False)
    label = console.cwd_label()
    assert "Current directory" in label


def test_print_info_outputs(capsys):
    console = Console(yes=True, dry_run=False)
    console.print_info("hello world")
    captured = capsys.readouterr()
    assert "hello world" in captured.out


def test_confirm_and_run_dry_run_prints_not_executed(capsys):
    console = Console(yes=False, dry_run=True)
    console.confirm_and_run("ls -la")
    out = capsys.readouterr().out
    assert "[dry-run]" in out
    assert "not executed" in out


def test_confirm_and_run_yes_mode_runs(capsys):
    console = Console(yes=True, dry_run=False)
    with patch("subprocess.run") as mock_run:
        console.confirm_and_run("echo hi")
        mock_run.assert_called_once()


def test_confirm_and_run_interactive_cancel(capsys):
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", return_value="n"):
        console.confirm_and_run("rm foo")
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_confirm_and_run_with_delete_path_yes(capsys):
    console = Console(yes=True, dry_run=False)
    with patch("subprocess.run"):
        console.confirm_and_run("rm foo", delete_path="foo")


def test_confirm_and_run_with_delete_path_declined(capsys):
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", return_value="n"):
        console.confirm_and_run("rm foo", delete_path="foo")
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_confirm_and_run_interactive_y_runs(capsys):
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", return_value="y"):
        with patch("subprocess.run") as mock_run:
            console.confirm_and_run("echo hi")
            mock_run.assert_called_once()


def test_confirm_and_run_interactive_eof_cancels(capsys):
    console = Console(yes=False, dry_run=False)
    with patch("builtins.input", side_effect=EOFError):
        console.confirm_and_run("echo hi")
    out = capsys.readouterr().out
    assert "Cancelled." in out
