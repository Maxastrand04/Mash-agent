import pytest
import sys
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_llm_failure_prints_message_no_traceback(test_tree, monkeypatch):
    monkeypatch.chdir(test_tree)
    sys.path.insert(0, str(PROJECT_ROOT))

    with patch("sys.argv", ["mash", "move", "notes", "to", "reports"]):
        with patch("mash.helpers.selection.source_selector.SourceSelector.select") as src_sel:
            src_sel.return_value = "./archive/notes.txt"
            with patch("mash.helpers.selection.destination_selector.DestinationSelector.select") as dst_sel:
                dst_sel.return_value = ("./reports", False)
                with patch("ollama.chat", side_effect=ConnectionError("refused")):
                    from mash.mash_cli import MashCLI
                    output = StringIO()
                    with redirect_stdout(output):
                        try:
                            MashCLI().run()
                        except SystemExit:
                            pass
    out = output.getvalue()
    assert "LLM not working, please try again" in out
    assert "Traceback" not in out


def test_llm_failure_exits_with_code_1(test_tree, monkeypatch):
    monkeypatch.chdir(test_tree)

    with patch("sys.argv", ["mash", "move", "notes", "to", "reports"]):
        with patch("mash.helpers.selection.source_selector.SourceSelector.select") as src_sel:
            src_sel.return_value = "./archive/notes.txt"
            with patch("mash.helpers.selection.destination_selector.DestinationSelector.select") as dst_sel:
                dst_sel.return_value = ("./reports", False)
                with patch("ollama.chat", side_effect=ConnectionError("refused")):
                    from mash.mash_cli import MashCLI
                    with pytest.raises(SystemExit) as exc_info:
                        MashCLI().run()
                    assert exc_info.value.code == 1
