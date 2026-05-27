import pytest
from unittest.mock import MagicMock, patch
from mash.flows.action_menu import ActionMenu
from mash.exceptions import UserCancelled, InvalidExtension


FAKE_CONTEXT = ".\nfoo.txt\nreports"


def make_action_menu(answer="", run_with_args=None):
    console = MagicMock()
    console.yes = False
    console.dry_run = False
    console.abs_path.side_effect = lambda p: f"/abs/{p}"
    console.cwd_label.return_value = "/cwd  (Current directory)"
    console.render_menu.return_value = "menu"
    console.ask_input.return_value = answer
    disambiguator = MagicMock()
    create_kind_picker = MagicMock()
    create_kind_picker.pick.return_value = "file"
    extension_picker = MagicMock()
    extension_picker.pick.return_value = "txt"
    reconciler = MagicMock()
    destination_selector = MagicMock()
    destination_selector.select.return_value = ("./reports", False)
    if run_with_args is None:
        run_with_args = MagicMock()
    return ActionMenu(
        console, disambiguator, create_kind_picker, extension_picker,
        reconciler, destination_selector, run_with_args
    )


def test_action_set_file_returns_open_cat():
    menu = make_action_menu()
    actions = menu.action_set(is_directory=False)
    verbs = [code for _, code in actions]
    assert "open" in verbs
    assert "cat" in verbs
    assert "rename" in verbs
    assert "go_into" not in verbs


def test_action_set_directory_returns_go_into():
    menu = make_action_menu()
    actions = menu.action_set(is_directory=True)
    verbs = [code for _, code in actions]
    assert "go_into" in verbs
    assert "list" in verbs
    assert "open" not in verbs


def test_show_empty_input_cancels(capsys):
    menu = make_action_menu(answer="")
    menu.show("./foo.txt", False, FAKE_CONTEXT)
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_show_typed_calls_run_with_args():
    run_fn = MagicMock()
    menu = make_action_menu(answer="move foo to bar", run_with_args=run_fn)
    menu.show("./foo.txt", False, FAKE_CONTEXT)
    run_fn.assert_called_once()


def test_execute_open_calls_confirm_and_run():
    menu = make_action_menu()
    menu.console.confirm_action.return_value = True
    menu.execute("open", "./foo.txt", False, FAKE_CONTEXT)
    menu.console.confirm_and_run.assert_called_once()


def test_execute_cat_calls_confirm_and_run():
    menu = make_action_menu()
    menu.console.confirm_action.return_value = True
    menu.execute("cat", "./foo.txt", False, FAKE_CONTEXT)
    menu.console.confirm_and_run.assert_called_once()


def test_execute_open_declined_prints_cancelled(capsys):
    menu = make_action_menu()
    menu.console.confirm_action.return_value = False
    menu.execute("open", "./foo.txt", False, FAKE_CONTEXT)
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_execute_remove_file_calls_confirm_and_run():
    menu = make_action_menu()
    menu.execute("remove", "./foo.txt", False, FAKE_CONTEXT)
    menu.console.confirm_and_run.assert_called_once()


def test_execute_remove_folder_uses_rf():
    menu = make_action_menu()
    menu.execute("remove", "./reports", True, FAKE_CONTEXT)
    call_args = menu.console.confirm_and_run.call_args[0][0]
    assert "rm -rf" in call_args


def test_execute_go_into_calls_run_with_args():
    run_fn = MagicMock()
    menu = make_action_menu(run_with_args=run_fn)
    menu.execute("go_into", "./reports", True, FAKE_CONTEXT)
    run_fn.assert_called_once()


def test_execute_move_calls_confirm_and_run():
    menu = make_action_menu()
    menu.execute("move", "./foo.txt", False, FAKE_CONTEXT)
    menu.console.confirm_and_run.assert_called_once()


def test_execute_rename_empty_input_cancels(capsys):
    menu = make_action_menu(answer="")
    menu.execute("rename", "./foo.txt", False, FAKE_CONTEXT)
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_execute_rename_calls_confirm_and_run():
    menu = make_action_menu(answer="bar.txt")
    menu.execute("rename", "./foo.txt", False, FAKE_CONTEXT)
    menu.console.confirm_and_run.assert_called_once()


def test_execute_chmod_calls_confirm_and_run():
    menu = make_action_menu(answer="755")
    menu.execute("chmod", "./foo.txt", False, FAKE_CONTEXT)
    menu.console.confirm_and_run.assert_called_once()


def test_execute_chmod_empty_cancels(capsys):
    menu = make_action_menu(answer="")
    menu.execute("chmod", "./foo.txt", False, FAKE_CONTEXT)
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_execute_add_file_name_with_ext_calls_confirm_and_run():
    menu = make_action_menu(answer="newfile.txt")
    menu.execute("add", "./reports", True, FAKE_CONTEXT)
    menu.console.confirm_and_run.assert_called_once()


def test_execute_add_empty_name_cancels(capsys):
    console = MagicMock()
    console.yes = False
    console.dry_run = False
    console.abs_path.side_effect = lambda p: f"/abs/{p}"
    console.render_menu.return_value = "menu"
    console.ask_input.return_value = ""
    menu = ActionMenu(
        console, MagicMock(), MagicMock(), MagicMock(),
        MagicMock(), MagicMock(), MagicMock()
    )
    menu.create_kind_picker.pick.return_value = "file"
    menu.execute("add", "./reports", True, FAKE_CONTEXT)
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_show_out_of_range_number_calls_run_with_args():
    run_fn = MagicMock()
    menu = make_action_menu(answer="99", run_with_args=run_fn)
    menu.show("./foo.txt", False, FAKE_CONTEXT)
    run_fn.assert_called_once()


def test_show_valid_number_calls_execute():
    menu = make_action_menu(answer="1")
    menu.console.confirm_action.return_value = True
    menu.show("./foo.txt", False, FAKE_CONTEXT)
    menu.console.confirm_and_run.assert_called_once()


def test_execute_add_kind_picker_cancel_prints_cancelled(capsys):
    from mash.exceptions import UserCancelled
    menu = make_action_menu()
    menu.create_kind_picker.pick.side_effect = UserCancelled()
    menu.execute("add", "./reports", True, FAKE_CONTEXT)
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_execute_add_folder_kind_calls_mkdir(capsys):
    menu = make_action_menu(answer="myfolder")
    menu.create_kind_picker.pick.return_value = "folder"
    menu.execute("add", "./reports", True, FAKE_CONTEXT)
    call_args = menu.console.confirm_and_run.call_args[0][0]
    assert "mkdir -p" in call_args


def test_execute_add_file_no_ext_picker_cancel_prints_cancelled(capsys):
    from mash.exceptions import UserCancelled
    menu = make_action_menu(answer="newfile")
    menu.create_kind_picker.pick.return_value = "file"
    menu.extension_picker.pick.side_effect = UserCancelled()
    menu.execute("add", "./reports", True, FAKE_CONTEXT)
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_execute_rename_with_reconciler_cancel(capsys):
    menu = make_action_menu(answer="bar.md")
    from mash.exceptions import UserCancelled
    menu.rename_extension_reconciler.reconcile.side_effect = UserCancelled()
    menu.execute("rename", "./foo.txt", False, FAKE_CONTEXT)
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_execute_copy_calls_confirm_and_run():
    menu = make_action_menu()
    menu.execute("copy", "./foo.txt", False, FAKE_CONTEXT)
    menu.console.confirm_and_run.assert_called_once()


def test_execute_move_cancelled_prints_cancelled(capsys):
    from mash.exceptions import UserCancelled
    menu = make_action_menu()
    menu.destination_selector.select.side_effect = UserCancelled()
    menu.execute("move", "./foo.txt", False, FAKE_CONTEXT)
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_execute_cat_declined_prints_cancelled(capsys):
    menu = make_action_menu()
    menu.console.confirm_action.return_value = False
    menu.execute("cat", "./foo.txt", False, FAKE_CONTEXT)
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_execute_unknown_action_does_nothing():
    menu = make_action_menu()
    menu.execute("unknown_action", "./foo.txt", False, FAKE_CONTEXT)
    menu.console.confirm_and_run.assert_not_called()


def test_execute_list_calls_run_with_args():
    run_fn = MagicMock()
    menu = make_action_menu(run_with_args=run_fn)
    menu.execute("list", "./reports", True, FAKE_CONTEXT)
    run_fn.assert_called_once()


def test_execute_add_file_no_ext_picker_succeeds_appends_extension():
    menu = make_action_menu(answer="newfile")
    menu.extension_picker.pick.return_value = "py"
    menu.execute("add", "./reports", True, FAKE_CONTEXT)
    call_arg = menu.console.confirm_and_run.call_args[0][0]
    assert "newfile.py" in call_arg
