import pytest
from unittest.mock import MagicMock
from mash.helpers.selection.create_kind_picker import CreateKindPicker
from mash.exceptions import UserCancelled


def make_console(yes=False, dry_run=False, answer=None):
    c = MagicMock()
    c.yes = yes
    c.dry_run = dry_run
    c.ask_input.return_value = answer or ""
    c.render_menu.return_value = "menu prompt"
    return c


def test_pick_yes_mode_returns_file():
    console = make_console(yes=True)
    picker = CreateKindPicker(console)
    assert picker.pick() == "file"


def test_pick_dry_run_mode_returns_file():
    console = make_console(dry_run=True)
    picker = CreateKindPicker(console)
    assert picker.pick() == "file"


def test_pick_interactive_1_returns_file():
    console = make_console(answer="1")
    picker = CreateKindPicker(console)
    assert picker.pick() == "file"


def test_pick_interactive_2_returns_folder():
    console = make_console(answer="2")
    picker = CreateKindPicker(console)
    assert picker.pick() == "folder"


def test_pick_interactive_empty_raises_user_cancelled():
    console = make_console(answer="")
    picker = CreateKindPicker(console)
    with pytest.raises(UserCancelled):
        picker.pick()


def test_pick_interactive_invalid_raises_user_cancelled():
    console = make_console(answer="x")
    picker = CreateKindPicker(console)
    with pytest.raises(UserCancelled):
        picker.pick()
