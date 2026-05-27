import pytest
from unittest.mock import MagicMock
from mash.helpers.selection.rename_extension_reconciler import RenameExtensionReconciler
from mash.exceptions import UserCancelled


def make_console(yes=False, dry_run=False, answer=None):
    c = MagicMock()
    c.yes = yes
    c.dry_run = dry_run
    c.ask_input.return_value = answer if answer is not None else ""
    return c


def test_reconcile_different_extension_yes_keeps():
    console = make_console(yes=True)
    r = RenameExtensionReconciler(console)
    result = r.reconcile("/x/foo.txt", "foo.md", ".txt", ".md", "different_extension")
    assert result == "foo.txt"


def test_reconcile_add_extension_yes_keeps_no_ext():
    console = make_console(yes=True)
    r = RenameExtensionReconciler(console)
    result = r.reconcile("/x/foo", "foo.py", "", ".py", "add_extension")
    assert result == "foo"


def test_reconcile_different_extension_interactive_option_1():
    console = make_console(answer="1")
    r = RenameExtensionReconciler(console)
    result = r.reconcile("/x/foo.txt", "foo.md", ".txt", ".md", "different_extension")
    assert result == "foo.txt"


def test_reconcile_different_extension_interactive_option_2():
    console = make_console(answer="2")
    r = RenameExtensionReconciler(console)
    result = r.reconcile("/x/foo.txt", "foo.md", ".txt", ".md", "different_extension")
    assert result == "foo.md"


def test_reconcile_different_extension_interactive_option_3_raises():
    console = make_console(answer="3")
    r = RenameExtensionReconciler(console)
    with pytest.raises(UserCancelled):
        r.reconcile("/x/foo.txt", "foo.md", ".txt", ".md", "different_extension")


def test_reconcile_different_extension_interactive_empty_raises():
    console = make_console(answer="")
    r = RenameExtensionReconciler(console)
    with pytest.raises(UserCancelled):
        r.reconcile("/x/foo.txt", "foo.md", ".txt", ".md", "different_extension")


def test_reconcile_add_extension_interactive_option_1_keeps_no_ext():
    console = make_console(answer="1")
    r = RenameExtensionReconciler(console)
    result = r.reconcile("/x/foo", "foo.py", "", ".py", "add_extension")
    assert result == "foo"


def test_reconcile_add_extension_interactive_option_2_adds_ext():
    console = make_console(answer="2")
    r = RenameExtensionReconciler(console)
    result = r.reconcile("/x/foo", "foo.py", "", ".py", "add_extension")
    assert result == "foo.py"


def test_reconcile_add_extension_interactive_empty_raises():
    console = make_console(answer="")
    r = RenameExtensionReconciler(console)
    with pytest.raises(UserCancelled):
        r.reconcile("/x/foo", "foo.py", "", ".py", "add_extension")


def test_reconcile_dry_run_keeps():
    console = make_console(dry_run=True)
    r = RenameExtensionReconciler(console)
    result = r.reconcile("/x/foo.txt", "foo.md", ".txt", ".md", "different_extension")
    assert result == "foo.txt"


def test_reconcile_add_extension_interactive_option_3_raises():
    console = make_console(answer="3")
    r = RenameExtensionReconciler(console)
    with pytest.raises(UserCancelled):
        r.reconcile("/x/foo", "foo.py", "", ".py", "add_extension")
