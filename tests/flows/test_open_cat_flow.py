import pytest
from unittest.mock import MagicMock
from mash.flows.open_cat_flow import OpenCatFlow
from mash.intent import Intent
from mash.exceptions import UserCancelled, SourceNotFound


FAKE_CONTEXT = ".\nfoo.txt\ndocs/readme.md"


def make_flow(source_return="./foo.txt", run_with_args=None):
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    console.abs_path.side_effect = lambda p: f"/abs/{p}"
    console.confirm_action.return_value = True
    llm = MagicMock()
    source_sel = MagicMock()
    source_sel.select.return_value = source_return
    disambiguator = MagicMock()
    if run_with_args is None:
        run_with_args = MagicMock()
    return OpenCatFlow(console, llm, source_sel, disambiguator, run_with_args, FAKE_CONTEXT)


def test_run_open_returns_command():
    flow = make_flow()
    intent = Intent.parse(["open", "foo"])
    result = flow.run(intent)
    assert result == "open ./foo.txt"


def test_run_cat_returns_command():
    flow = make_flow()
    intent = Intent.parse(["cat", "foo"])
    result = flow.run(intent)
    assert result == "cat ./foo.txt"


def test_run_show_contents_of():
    flow = make_flow(source_return="./docs/readme.md")
    intent = Intent.parse(["show", "contents", "of", "readme"])
    intent = Intent(verb="cat", args=["show", "contents", "of", "readme.md"],
                    filtered_args=["show", "contents", "of", "readme.md"],
                    dest_token=None, rename_target=None,
                    is_create_file=False, is_create_folder=False)
    result = flow.run(intent)
    assert result is not None


def test_run_cancel_source_returns_none(capsys):
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    console.abs_path.side_effect = lambda p: p
    source_sel = MagicMock()
    source_sel.select.side_effect = UserCancelled()
    disambiguator = MagicMock()
    flow = OpenCatFlow(console, MagicMock(), source_sel, disambiguator, MagicMock(), FAKE_CONTEXT)
    intent = Intent.parse(["open", "foo"])
    result = flow.run(intent)
    assert result is None
    assert "Cancelled." in capsys.readouterr().out


def test_run_source_not_found_yes_mode_returns_none(capsys):
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    source_sel = MagicMock()
    disambiguator = MagicMock()
    flow = OpenCatFlow(console, MagicMock(), source_sel, disambiguator, MagicMock(), FAKE_CONTEXT)
    intent = Intent.parse(["open", "zzznomatch"])
    result = flow.run(intent)
    assert result is None


def test_run_source_not_found_calls_handle(capsys):
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    source_sel = MagicMock()
    disambiguator = MagicMock()
    flow = OpenCatFlow(console, MagicMock(), source_sel, disambiguator, MagicMock(), FAKE_CONTEXT)
    intent = Intent.parse(["open", "zzznomatch"])
    result = flow.run(intent)
    assert result is None
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_run_source_not_found_from_selector(capsys):
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    console.abs_path.side_effect = lambda p: p
    source_sel = MagicMock()
    source_sel.select.side_effect = SourceNotFound("foo")
    disambiguator = MagicMock()
    flow = OpenCatFlow(console, MagicMock(), source_sel, disambiguator, MagicMock(), FAKE_CONTEXT)
    intent = Intent.parse(["open", "foo"])
    result = flow.run(intent)
    assert result is None
    assert "Cancelled." in capsys.readouterr().out


def test_run_stop_word_in_args_skipped():
    flow = make_flow(source_return="./foo.txt")
    intent = Intent(
        verb="open", args=["open", "the", "foo.txt"],
        filtered_args=["open", "the", "foo.txt"],
        dest_token=None, rename_target=None,
        is_create_file=False, is_create_folder=False,
    )
    result = flow.run(intent)
    assert result is not None


def test_handle_not_found_interactive_calls_run_with_args():
    run_fn = MagicMock()
    console = MagicMock()
    console.yes = False
    console.dry_run = False
    from mash.helpers.selection.disambiguator import Selection
    disambiguator = MagicMock()
    disambiguator.pick_not_found.return_value = Selection(kind="typed", value="./other.txt")
    flow = OpenCatFlow(console, MagicMock(), MagicMock(), disambiguator, run_fn, FAKE_CONTEXT)
    intent = Intent.parse(["open", "zzznomatch"])
    flow.run(intent)
    run_fn.assert_called_once_with(["./other.txt"])
