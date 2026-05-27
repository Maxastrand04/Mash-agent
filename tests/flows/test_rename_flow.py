import pytest
from unittest.mock import MagicMock, patch
from mash.flows.rename_flow import RenameFlow
from mash.intent import Intent
from mash.exceptions import UserCancelled, SourceNotFound


FAKE_CONTEXT = ".\nfoo.txt\nbar.md"


def make_flow(llm_response="mv foo.txt ./bar.txt", source="./foo.txt", reconcile_result=None):
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = llm_response
    source_sel = MagicMock()
    source_sel.select.return_value = source
    reconciler = MagicMock()
    if reconcile_result is not None:
        reconciler.reconcile.return_value = reconcile_result
    return RenameFlow(console, llm, source_sel, reconciler, FAKE_CONTEXT)


def test_run_same_extension_returns_command():
    flow = make_flow()
    intent = Intent.parse(["rename", "foo.txt", "to", "bar.txt"])
    result = flow.run(intent)
    assert result is not None
    assert "mv" in result


def test_run_cancel_source_returns_none(capsys):
    console = MagicMock()
    console.yes = False
    llm = MagicMock()
    source_sel = MagicMock()
    source_sel.select.side_effect = UserCancelled()
    reconciler = MagicMock()
    flow = RenameFlow(console, llm, source_sel, reconciler, FAKE_CONTEXT)
    intent = Intent.parse(["rename", "foo.txt", "to", "bar.txt"])
    result = flow.run(intent)
    assert result is None
    assert "Cancelled." in capsys.readouterr().out


def test_run_source_not_found_returns_none(capsys):
    console = MagicMock()
    console.yes = True
    llm = MagicMock()
    source_sel = MagicMock()
    source_sel.select.side_effect = SourceNotFound("foo")
    reconciler = MagicMock()
    flow = RenameFlow(console, llm, source_sel, reconciler, FAKE_CONTEXT)
    intent = Intent.parse(["rename", "foo", "to", "bar"])
    result = flow.run(intent)
    assert result is None


def test_run_different_extension_uses_reconciler():
    reconciler = MagicMock()
    reconciler.reconcile.return_value = "bar.txt"
    console = MagicMock()
    console.yes = True
    llm = MagicMock()
    llm.ask.return_value = "mv foo.txt ./bar.txt"
    source_sel = MagicMock()
    source_sel.select.return_value = "./foo.txt"
    flow = RenameFlow(console, llm, source_sel, reconciler, FAKE_CONTEXT)
    intent = Intent.parse(["rename", "foo.txt", "to", "bar.md"])
    result = flow.run(intent)
    reconciler.reconcile.assert_called_once()
    assert result is not None


def test_run_reconciler_cancel_returns_none(capsys):
    reconciler = MagicMock()
    reconciler.reconcile.side_effect = UserCancelled()
    console = MagicMock()
    console.yes = False
    llm = MagicMock()
    source_sel = MagicMock()
    source_sel.select.return_value = "./foo.txt"
    flow = RenameFlow(console, llm, source_sel, reconciler, FAKE_CONTEXT)
    intent = Intent.parse(["rename", "foo.txt", "to", "bar.md"])
    result = flow.run(intent)
    assert result is None


def test_run_llm_empty_raises_llm_unavailable():
    console = MagicMock()
    llm = MagicMock()
    llm.ask.return_value = ""
    source_sel = MagicMock()
    source_sel.select.return_value = "./foo.txt"
    reconciler = MagicMock()
    flow = RenameFlow(console, llm, source_sel, reconciler, FAKE_CONTEXT)
    intent = Intent.parse(["rename", "foo.txt", "to", "bar.txt"])
    from mash.exceptions import LLMUnavailable
    with pytest.raises(LLMUnavailable):
        flow.run(intent)


def test_run_strips_mkdir_from_chained():
    flow = make_flow(llm_response="mkdir -p tmp && mv ./foo.txt ./bar.txt")
    intent = Intent.parse(["rename", "foo.txt", "to", "bar.txt"])
    result = flow.run(intent)
    assert result is not None
    assert "mkdir" not in result


def test_run_all_mkdir_chained_keeps_command():
    flow = make_flow(llm_response="mkdir -p tmp && mkdir -p bar")
    intent = Intent.parse(["rename", "foo.txt", "to", "bar.txt"])
    result = flow.run(intent)
    assert result is not None
