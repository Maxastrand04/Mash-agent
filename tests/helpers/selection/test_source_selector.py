import pytest
from unittest.mock import MagicMock
from mash.helpers.selection.source_selector import SourceSelector
from mash.helpers.selection.disambiguator import Selection
from mash.exceptions import UserCancelled, SourceNotFound


FAKE_CONTEXT = ".\nfoo.txt\nbar.py"


def make_console(yes=True, dry_run=False):
    c = MagicMock()
    c.yes = yes
    c.dry_run = dry_run
    return c


def make_disambiguator(selections=None):
    d = MagicMock()
    if selections:
        d.pick_from_hits.side_effect = [Selection(kind=k, value=v) for k, v in selections]
        d.pick_not_found.side_effect = [Selection(kind=k, value=v) for k, v in selections]
    return d


def test_select_yes_mode_returns_first_candidate(capsys):
    console = make_console(yes=True)
    selector = SourceSelector(console, MagicMock())
    result = selector.select(["foo.txt", "bar.py"], FAKE_CONTEXT)
    assert result == "foo.txt"


def test_select_yes_mode_no_candidates_raises_source_not_found():
    console = make_console(yes=True)
    selector = SourceSelector(console, MagicMock())
    with pytest.raises(SourceNotFound):
        selector.select([], FAKE_CONTEXT, query="missing")


def test_select_dry_run_returns_first_candidate(capsys):
    console = make_console(yes=False, dry_run=True)
    selector = SourceSelector(console, MagicMock())
    result = selector.select(["foo.txt"], FAKE_CONTEXT)
    assert result == "foo.txt"


def test_select_interactive_selected():
    console = make_console(yes=False)
    d = MagicMock()
    d.pick_from_hits.return_value = Selection(kind="selected", value="foo.txt")
    selector = SourceSelector(console, d)
    result = selector.select(["foo.txt", "bar.py"], FAKE_CONTEXT)
    assert result == "foo.txt"


def test_select_interactive_cancel_raises_user_cancelled():
    console = make_console(yes=False)
    d = MagicMock()
    d.pick_from_hits.side_effect = UserCancelled()
    selector = SourceSelector(console, d)
    with pytest.raises(UserCancelled):
        selector.select(["foo.txt"], FAKE_CONTEXT)


def test_select_interactive_typed_refines_candidates():
    console = make_console(yes=False)
    d = MagicMock()
    d.pick_from_hits.side_effect = [
        Selection(kind="typed", value="foo"),
        Selection(kind="selected", value="foo.txt"),
    ]
    selector = SourceSelector(console, d)
    result = selector.select(["bar.py"], ".\nfoo.txt\nbar.py")
    assert result == "foo.txt"


def test_select_interactive_not_found_then_typed():
    console = make_console(yes=False)
    d = MagicMock()
    d.pick_not_found.return_value = Selection(kind="typed", value="foo")
    d.pick_from_hits.return_value = Selection(kind="selected", value="foo.txt")
    selector = SourceSelector(console, d)
    result = selector.select([], ".\nfoo.txt", query="missing")
    assert result == "foo.txt"
