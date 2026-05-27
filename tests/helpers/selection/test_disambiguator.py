import pytest
from unittest.mock import MagicMock
from mash.helpers.selection.disambiguator import Disambiguator, Selection
from mash.exceptions import UserCancelled


def make_console(yes=True, dry_run=False, inputs=None):
    console = MagicMock()
    console.yes = yes
    console.dry_run = dry_run
    if inputs is not None:
        console.ask_input.side_effect = inputs
    console.abs_path.side_effect = lambda p: f"/abs/{p}"
    console.render_menu.return_value = "menu prompt"
    return console


def test_pick_from_hits_single_numeric_input():
    console = make_console(yes=False, inputs=["1"])
    d = Disambiguator(console)
    result = d.pick_from_hits(["a.txt", "b.txt"], term="a", kind="file")
    assert result.kind == "selected"
    assert result.value == "a.txt"


def test_pick_from_hits_second_option():
    console = make_console(yes=False, inputs=["2"])
    d = Disambiguator(console)
    result = d.pick_from_hits(["a.txt", "b.txt"], term=None, kind="file")
    assert result.kind == "selected"
    assert result.value == "b.txt"


def test_pick_from_hits_empty_input_raises_user_cancelled():
    console = make_console(yes=False, inputs=[""])
    d = Disambiguator(console)
    with pytest.raises(UserCancelled):
        d.pick_from_hits(["a.txt"], term="a", kind="file")


def test_pick_from_hits_typed_free_text():
    console = make_console(yes=False, inputs=["newquery"])
    d = Disambiguator(console)
    result = d.pick_from_hits(["a.txt"], term="a", kind="file")
    assert result.kind == "typed"
    assert result.value == "newquery"


def test_pick_from_hits_out_of_range_returns_typed():
    console = make_console(yes=False, inputs=["99"])
    d = Disambiguator(console)
    result = d.pick_from_hits(["a.txt"], term="a", kind="file")
    assert result.kind == "typed"
    assert result.value == "99"


def test_pick_not_found_typed_value():
    console = make_console(yes=False, inputs=["newterm"])
    d = Disambiguator(console)
    result = d.pick_not_found(term="x")
    assert result.kind == "typed"
    assert result.value == "newterm"


def test_pick_not_found_empty_raises_user_cancelled():
    console = make_console(yes=False, inputs=[""])
    d = Disambiguator(console)
    with pytest.raises(UserCancelled):
        d.pick_not_found(term="x")


def test_pick_with_actions_selects_hit():
    console = make_console(yes=False, inputs=["1"])
    d = Disambiguator(console)
    result = d.pick_with_actions(
        hits=["path/a"],
        actions=[("open", "open_action")],
        header="Choose:",
    )
    assert result.kind == "selected"
    assert result.value == "path/a"


def test_pick_with_actions_selects_action():
    console = make_console(yes=False, inputs=["2"])
    d = Disambiguator(console)
    result = d.pick_with_actions(
        hits=["path/a"],
        actions=[("action one", "act1")],
        header="Choose:",
    )
    assert result.kind == "action"
    assert result.value == "act1"


def test_pick_with_actions_empty_raises_cancelled():
    console = make_console(yes=False, inputs=[""])
    d = Disambiguator(console)
    with pytest.raises(UserCancelled):
        d.pick_with_actions(hits=[], actions=[("act", "a")], header="h")


def test_pick_with_actions_typed_free_text():
    console = make_console(yes=False, inputs=["query"])
    d = Disambiguator(console)
    result = d.pick_with_actions(hits=[], actions=[("act", "a")], header="h")
    assert result.kind == "typed"
    assert result.value == "query"


def test_parse_selection_valid():
    assert Disambiguator._parse_selection("1", 3) == 0
    assert Disambiguator._parse_selection("3", 3) == 2


def test_parse_selection_out_of_range():
    assert Disambiguator._parse_selection("5", 3) is None
    assert Disambiguator._parse_selection("0", 3) is None


def test_parse_selection_non_numeric():
    assert Disambiguator._parse_selection("abc", 3) is None


def test_pick_from_hits_no_term_header():
    console = make_console(yes=False, inputs=["1"])
    d = Disambiguator(console)
    d.pick_from_hits(["a.txt"], term=None, kind="file")
    console.render_menu.assert_called_once()
    call_args = console.render_menu.call_args[0]
    assert "term" not in call_args[0]


def test_pick_from_hits_single_result_header():
    console = make_console(yes=False, inputs=["1"])
    d = Disambiguator(console)
    d.pick_from_hits(["a.txt"], term="foo", kind="folder")
    call_args = console.render_menu.call_args[0]
    assert "found a folder" in call_args[0]


def test_pick_from_hits_multiple_results_header():
    console = make_console(yes=False, inputs=["1"])
    d = Disambiguator(console)
    d.pick_from_hits(["a.txt", "b.txt"], term="foo", kind="file")
    call_args = console.render_menu.call_args[0]
    assert "2 files" in call_args[0]
