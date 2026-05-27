import pytest
from unittest.mock import MagicMock, patch
from mash.flows.move_copy_flow import MoveCopyFlow
from mash.intent import Intent
from mash.exceptions import UserCancelled, SourceNotFound, DestinationNotFound


FAKE_CONTEXT = ".\nfoo.txt\nreports"


def make_console(yes=True, dry_run=False):
    c = MagicMock()
    c.yes = yes
    c.dry_run = dry_run
    return c


def make_flow(llm_response="mv ./foo.txt ./reports/", source="./foo.txt", destination=("./reports", False)):
    console = make_console()
    llm = MagicMock()
    llm.ask.return_value = llm_response
    source_sel = MagicMock()
    source_sel.select.return_value = source
    dest_sel = MagicMock()
    dest_sel.select.return_value = destination
    return MoveCopyFlow(console, llm, source_sel, dest_sel, FAKE_CONTEXT)


def test_run_move_returns_command():
    flow = make_flow()
    intent = Intent.parse(["move", "foo", "to", "reports"])
    with patch("os.path.isfile", return_value=True), patch("os.path.isdir", return_value=False):
        result = flow.run(intent)
    assert result is not None
    assert "mv" in result or "foo" in result


def test_run_cancel_source_returns_none(capsys):
    console = make_console(yes=False)
    llm = MagicMock()
    source_sel = MagicMock()
    source_sel.select.side_effect = UserCancelled()
    dest_sel = MagicMock()
    flow = MoveCopyFlow(console, llm, source_sel, dest_sel, FAKE_CONTEXT)
    intent = Intent.parse(["move", "foo", "to", "reports"])
    result = flow.run(intent)
    assert result is None
    assert "Cancelled." in capsys.readouterr().out


def test_run_source_not_found_returns_none(capsys):
    console = make_console(yes=True)
    llm = MagicMock()
    source_sel = MagicMock()
    source_sel.select.side_effect = SourceNotFound("foo")
    dest_sel = MagicMock()
    flow = MoveCopyFlow(console, llm, source_sel, dest_sel, FAKE_CONTEXT)
    intent = Intent.parse(["move", "foo", "to", "reports"])
    result = flow.run(intent)
    assert result is None


def test_run_dest_not_found_returns_none(capsys):
    console = make_console(yes=True)
    llm = MagicMock()
    source_sel = MagicMock()
    source_sel.select.return_value = "./foo.txt"
    dest_sel = MagicMock()
    dest_sel.select.side_effect = DestinationNotFound("nowhere")
    flow = MoveCopyFlow(console, llm, source_sel, dest_sel, FAKE_CONTEXT)
    intent = Intent.parse(["move", "foo", "to", "nowhere"])
    result = flow.run(intent)
    assert result is None


def test_run_strips_mkdir_from_chained_command():
    flow = make_flow(llm_response="mkdir -p ./x && mv ./foo.txt ./x/")
    intent = Intent.parse(["move", "foo", "to", "x"])
    with patch("os.path.isfile", return_value=True), patch("os.path.isdir", return_value=False):
        result = flow.run(intent)
    assert "mkdir" not in result


def test_run_copy_intent():
    flow = make_flow(llm_response="cp ./foo.txt ./reports/")
    intent = Intent.parse(["copy", "foo", "to", "reports"])
    with patch("os.path.isfile", return_value=True), patch("os.path.isdir", return_value=False):
        result = flow.run(intent)
    assert result is not None


def test_run_source_none_skips_type_detection():
    flow = make_flow(source=None, destination=("./reports", False))
    intent = Intent.parse(["move", "foo", "to", "reports"])
    result = flow.run(intent)
    assert result is not None


def test_run_source_is_directory():
    flow = make_flow(source="./reports")
    intent = Intent.parse(["move", "reports", "to", "archive"])
    with patch("os.path.isfile", return_value=False), patch("os.path.isdir", return_value=True):
        result = flow.run(intent)
    assert result is not None


def test_run_all_mkdir_chained_keeps_command():
    flow = make_flow(llm_response="mkdir -p foo && mkdir -p bar")
    intent = Intent.parse(["move", "foo", "to", "bar"])
    result = flow.run(intent)
    assert "mkdir" in result


def test_run_destination_empty_skips_apply_destination():
    flow = make_flow(destination=("", False))
    intent = Intent.parse(["move", "foo", "to", "bar"])
    with patch("os.path.isfile", return_value=True), patch("os.path.isdir", return_value=False):
        result = flow.run(intent)
