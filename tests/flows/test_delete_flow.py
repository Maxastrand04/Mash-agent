import pytest
from unittest.mock import MagicMock, patch
from mash.flows.delete_flow import DeleteFlow
from mash.intent import Intent
from mash.exceptions import UserCancelled, SourceNotFound


FAKE_CONTEXT = ".\nfoo.txt\nreports"


def make_flow(llm_response="rm ./foo.txt", source="./foo.txt"):
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = llm_response
    source_sel = MagicMock()
    source_sel.select.return_value = source
    return DeleteFlow(console, llm, source_sel, FAKE_CONTEXT)


def test_run_returns_tuple():
    flow = make_flow()
    intent = Intent.parse(["delete", "foo"])
    with patch("os.path.isfile", return_value=True), patch("os.path.isdir", return_value=False):
        result = flow.run(intent)
    assert result is not None
    command, delete_path = result
    assert "rm" in command


def test_run_folder_returns_rf_command():
    flow = make_flow(llm_response="rm -rf ./reports", source="./reports")
    intent = Intent.parse(["delete", "reports"])
    with patch("os.path.isfile", return_value=False), patch("os.path.isdir", return_value=True):
        result = flow.run(intent)
    assert result is not None
    command, _ = result
    assert "rm -rf" in command


def test_run_cancel_returns_none(capsys):
    console = MagicMock()
    console.yes = False
    llm = MagicMock()
    source_sel = MagicMock()
    source_sel.select.side_effect = UserCancelled()
    flow = DeleteFlow(console, llm, source_sel, FAKE_CONTEXT)
    intent = Intent.parse(["delete", "foo"])
    result = flow.run(intent)
    assert result is None
    assert "Cancelled." in capsys.readouterr().out


def test_run_source_not_found_returns_none(capsys):
    console = MagicMock()
    console.yes = True
    llm = MagicMock()
    source_sel = MagicMock()
    source_sel.select.side_effect = SourceNotFound("foo")
    flow = DeleteFlow(console, llm, source_sel, FAKE_CONTEXT)
    intent = Intent.parse(["delete", "foo"])
    result = flow.run(intent)
    assert result is None


def test_run_strips_mkdir_from_chained():
    flow = make_flow(llm_response="mkdir -p tmp && rm ./foo.txt")
    intent = Intent.parse(["delete", "foo"])
    with patch("os.path.isfile", return_value=True), patch("os.path.isdir", return_value=False):
        result = flow.run(intent)
    command, _ = result
    assert "mkdir" not in command


def test_run_delete_path_set_when_rm():
    flow = make_flow(llm_response="rm ./foo.txt", source="./foo.txt")
    intent = Intent.parse(["delete", "foo"])
    with patch("os.path.isfile", return_value=True), patch("os.path.isdir", return_value=False):
        result = flow.run(intent)
    _, delete_path = result
    assert delete_path == "./foo.txt"


def test_run_source_none_skips_type_detection():
    flow = make_flow(source=None)
    intent = Intent.parse(["delete", "foo"])
    result = flow.run(intent)
    assert result is not None
    command, delete_path = result
    assert delete_path is None


def test_run_source_neither_file_nor_dir_is_unknown():
    flow = make_flow(source="./foo.txt")
    intent = Intent.parse(["delete", "foo"])
    with patch("os.path.isfile", return_value=False), patch("os.path.isdir", return_value=False):
        result = flow.run(intent)
    assert result is not None


def test_run_llm_empty_raises_llm_unavailable(capsys):
    console = MagicMock()
    llm = MagicMock()
    llm.ask.return_value = ""
    source_sel = MagicMock()
    source_sel.select.return_value = "./foo.txt"
    from mash.exceptions import LLMUnavailable
    flow = DeleteFlow(console, llm, source_sel, FAKE_CONTEXT)
    intent = Intent.parse(["delete", "foo"])
    with patch("os.path.isfile", return_value=True), patch("os.path.isdir", return_value=False):
        with pytest.raises(LLMUnavailable):
            flow._run(intent)


def test_run_all_mkdir_chained_keeps_command():
    flow = make_flow(llm_response="mkdir -p foo && mkdir -p bar")
    intent = Intent.parse(["delete", "foo"])
    with patch("os.path.isfile", return_value=True), patch("os.path.isdir", return_value=False):
        result = flow.run(intent)
    command, _ = result
    assert "mkdir" in command
