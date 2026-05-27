import pytest
from unittest.mock import MagicMock, patch
from mash.flows.create_flow import CreateFlow
from mash.intent import Intent
from mash.exceptions import UserCancelled, DestinationNotFound, InvalidExtension


FAKE_CONTEXT = ".\nreports\nfoo.py"


def make_flow(llm_response="touch ./foo.py", destination=(".", False),
              kind_pick="file", extension_pick="py"):
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = llm_response
    dest_sel = MagicMock()
    dest_sel.select.return_value = destination
    kind_picker = MagicMock()
    kind_picker.pick.return_value = kind_pick
    ext_picker = MagicMock()
    ext_picker.pick.return_value = extension_pick
    return CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)


def test_run_create_file_with_bare_path():
    flow = make_flow(llm_response="touch ./foo.py")
    intent = Intent.parse(["create", "foo.py"])
    result = flow.run(intent)
    assert result is not None
    assert "touch" in result
    assert "foo.py" in result


def test_run_create_folder():
    flow = make_flow(llm_response="mkdir -p ./exports", kind_pick="folder")
    intent = Intent.parse(["create", "folder", "exports"])
    result = flow.run(intent)
    assert result is not None
    assert "mkdir" in result


def test_run_cancel_dest_returns_none(capsys):
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    console.print_info = MagicMock()
    llm = MagicMock()
    dest_sel = MagicMock()
    dest_sel.select.side_effect = DestinationNotFound("nowhere")
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "foo.py"])
    result = flow.run(intent)
    assert result is None


def test_run_cancel_user_cancelled_returns_none(capsys):
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    console.print_info = MagicMock()
    llm = MagicMock()
    dest_sel = MagicMock()
    dest_sel.select.side_effect = UserCancelled()
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "foo.py"])
    result = flow.run(intent)
    assert result is None


def test_run_invalid_extension_returns_none():
    console = MagicMock()
    console.yes = False
    console.dry_run = False
    console.print_info = MagicMock()
    llm = MagicMock()
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    kind_picker.pick.return_value = "file"
    ext_picker = MagicMock()
    ext_picker.pick.side_effect = InvalidExtension("xyz123")
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "something"])
    result = flow.run(intent)
    assert result is None


def test_run_create_folder_in_destination():
    flow = make_flow(llm_response="mkdir -p ./reports/exports", destination=("./reports", False))
    intent = Intent.parse(["create", "folder", "exports", "in", "reports"])
    result = flow.run(intent)
    assert result is not None
    assert "mkdir" in result


def test_run_create_destination_with_mkdir_prefix():
    flow = make_flow(llm_response="touch ./newdir/foo.py", destination=("./newdir", True))
    intent = Intent.parse(["create", "file", "foo.py", "in", "newdir"])
    result = flow.run(intent)
    assert result is not None
    assert "mkdir" in result


def test_run_create_bare_filename_detected():
    flow = make_flow(llm_response="touch ./foo.py")
    intent = Intent.parse(["create", "foo.py"])
    result = flow.run(intent)
    assert result is not None
    assert "foo.py" in result


def test_run_create_kind_picker_file():
    flow = make_flow(llm_response="touch ./myfile.txt", kind_pick="file")
    intent = Intent.parse(["create", "myfile"])
    result = flow.run(intent)
    assert result is not None


def test_run_create_kind_picker_folder():
    flow = make_flow(llm_response="mkdir -p ./myfolder", kind_pick="folder")
    intent = Intent.parse(["create", "myfolder"])
    result = flow.run(intent)
    assert result is not None
    assert "myfolder" in result


def test_run_create_file_with_named_marker():
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = "touch ./my_report.py"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "named", "my", "report.py"])
    result = flow.run(intent)
    assert result is not None


def test_run_create_file_bare_path_with_lang_extension():
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = "touch ./myfile.py"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    kind_picker.pick.return_value = "file"
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "myfile", "python"])
    result = flow.run(intent)
    assert result is not None
    assert ".py" in result


def test_run_create_file_bare_path_with_picker_extension():
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = "touch ./myfile.txt"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    kind_picker.pick.return_value = "file"
    ext_picker = MagicMock()
    ext_picker.pick.return_value = "txt"
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "myfile"])
    result = flow.run(intent)
    assert result is not None
    assert ".txt" in result


def test_run_create_new_file_format_picker_yes():
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    console.ask_input = MagicMock()
    llm = MagicMock()
    llm.ask.return_value = "touch ./my_report.md"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "called", "my", "report", "markdown"])
    result = flow.run(intent)
    assert result is not None


def test_run_create_new_file_format_picker_choose_1():
    console = MagicMock()
    console.yes = False
    console.dry_run = False
    console.ask_input.return_value = "1"
    llm = MagicMock()
    llm.ask.return_value = "touch ./my_report.md"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "called", "my", "report", "markdown"])
    result = flow.run(intent)
    assert result is not None


def test_run_create_new_file_format_picker_cancel():
    console = MagicMock()
    console.yes = False
    console.dry_run = False
    console.ask_input.return_value = ""
    llm = MagicMock()
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "called", "my", "report", "markdown"])
    result = flow.run(intent)
    assert result is None


def test_run_create_new_file_format_manual_with_dot():
    console = MagicMock()
    console.yes = False
    console.dry_run = False
    console.ask_input.return_value = "MyCustom.md"
    llm = MagicMock()
    llm.ask.return_value = "touch ./MyCustom.md"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "called", "my", "report", "markdown"])
    result = flow.run(intent)
    assert result is not None


def test_run_create_new_file_format_manual_without_dot_picks_ext():
    console = MagicMock()
    console.yes = False
    console.dry_run = False
    console.ask_input.return_value = "mycustom"
    llm = MagicMock()
    llm.ask.return_value = "touch ./mycustom.md"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    ext_picker.pick.return_value = "txt"
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "called", "my", "report"])
    result = flow.run(intent)
    assert result is not None


def test_run_create_llm_empty_raises():
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = ""
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "foo.py"])
    from mash.exceptions import LLMUnavailable
    with pytest.raises(LLMUnavailable):
        flow._run(intent)


def test_run_create_with_and_in_command_strips_mkdir():
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = "mkdir -p tmp && touch ./foo.py"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "foo.py"])
    result = flow.run(intent)
    assert result is not None
    assert "mkdir" not in result


def test_run_create_new_file_with_ext_no_bare_path():
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = "touch ./my_report.md"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "called", "my", "report.md"])
    result = flow.run(intent)
    assert result is not None


def test_run_create_no_candidate_tokens_skips_kind_picker():
    flow = make_flow(llm_response="touch ./something")
    intent = Intent.parse(["create"])
    result = flow.run(intent)
    assert result is not None


def test_run_create_bare_path_with_marker_single_token():
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = "touch ./something.txt"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "called", "something"])
    result = flow.run(intent)
    assert result is not None


def test_run_create_bare_path_marker_stop_word_skips_bare():
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = "touch ./placeholder.txt"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    ext_picker.pick.return_value = "txt"
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "called", "to"])
    result = flow.run(intent)
    assert result is not None


def test_run_create_format_picker_manual_without_dot_with_extension():
    console = MagicMock()
    console.yes = False
    console.dry_run = False
    console.ask_input.return_value = "mycustom"
    llm = MagicMock()
    llm.ask.return_value = "touch ./mycustom.md"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "file", "called", "my", "report.md"])
    result = flow.run(intent)
    assert result is not None
    assert "mycustom" in result


def test_run_create_all_mkdir_chained_non_mkdir_empty():
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    llm = MagicMock()
    llm.ask.return_value = "mkdir -p foo && mkdir -p bar"
    dest_sel = MagicMock()
    dest_sel.select.return_value = (".", False)
    kind_picker = MagicMock()
    kind_picker.pick.return_value = "folder"
    ext_picker = MagicMock()
    flow = CreateFlow(console, llm, dest_sel, kind_picker, ext_picker, FAKE_CONTEXT)
    intent = Intent.parse(["create", "myfolder"])
    result = flow.run(intent)
    assert result is not None
