import pytest
from unittest.mock import MagicMock
from mash.helpers.selection.extension_picker import ExtensionPicker
from mash.exceptions import UserCancelled, InvalidExtension


def make_console(yes=False, dry_run=False, answer=None):
    c = MagicMock()
    c.yes = yes
    c.dry_run = dry_run
    c.ask_input.return_value = answer if answer is not None else ""
    return c


CONTEXT_WITH_PY = "a.py\nb.py\nc.md"
CONTEXT_EMPTY = ""


def test_pick_yes_returns_most_common_extension():
    console = make_console(yes=True)
    picker = ExtensionPicker(console)
    result = picker.pick(CONTEXT_WITH_PY)
    assert result == "py"


def test_pick_yes_empty_context_returns_txt():
    console = make_console(yes=True)
    picker = ExtensionPicker(console)
    result = picker.pick(CONTEXT_EMPTY)
    assert result == "txt"


def test_pick_dry_run_returns_most_common():
    console = make_console(dry_run=True)
    picker = ExtensionPicker(console)
    result = picker.pick(CONTEXT_WITH_PY)
    assert result == "py"


def test_pick_interactive_empty_raises_user_cancelled():
    console = make_console(answer="")
    picker = ExtensionPicker(console)
    with pytest.raises(UserCancelled):
        picker.pick(CONTEXT_WITH_PY)


def test_pick_interactive_numeric_selects_extension():
    console = make_console(answer="1")
    picker = ExtensionPicker(console)
    result = picker.pick(CONTEXT_WITH_PY)
    assert result == "py"


def test_pick_interactive_valid_manual_extension():
    console = make_console(answer="py")
    picker = ExtensionPicker(console)
    result = picker.pick(CONTEXT_EMPTY)
    assert result == "py"


def test_pick_interactive_unknown_manual_extension_raises():
    console = make_console(answer="xyz123unknown")
    picker = ExtensionPicker(console)
    with pytest.raises(InvalidExtension):
        picker.pick(CONTEXT_EMPTY)


def test_pick_interactive_non_numeric_with_context_falls_through_to_normalized():
    console = make_console(answer="py")
    picker = ExtensionPicker(console)
    result = picker.pick(CONTEXT_WITH_PY)
    assert result == "py"


def test_pick_interactive_out_of_range_number_falls_through_to_normalized():
    console = make_console(answer="99")
    picker = ExtensionPicker(console)
    with pytest.raises(InvalidExtension):
        picker.pick(CONTEXT_WITH_PY)
