import pytest
from unittest.mock import MagicMock, patch
from mash.flows.browse_mode import BrowseMode
from mash.exceptions import UserCancelled


def make_browse_mode(inputs=None):
    console = MagicMock()
    console.yes = False
    console.dry_run = False
    console.abs_path.side_effect = lambda p: f"/abs/{p}"
    console.cwd_label.return_value = "/cwd  (Current directory)"
    console.render_menu.return_value = "menu prompt"
    if inputs:
        console.ask_input.side_effect = inputs
    else:
        console.ask_input.return_value = ""
    disambiguator = MagicMock()
    list_scope = MagicMock()
    list_scope.list_entries.return_value = [("./foo.txt", False), ("./reports", True)]
    list_scope.scope_label.return_value = "."
    list_scope.scoped_context.return_value = ".\nfoo.txt\nreports"
    action_menu = MagicMock()
    return BrowseMode(console, disambiguator, list_scope, action_menu)


def test_run_yes_mode_prints_and_returns(capsys):
    console = MagicMock()
    console.yes = True
    console.dry_run = False
    console.abs_path.side_effect = lambda p: f"/abs/{p}"
    console.cwd_label.return_value = "/cwd  (Current directory)"
    console.render_menu.return_value = "menu"
    list_scope = MagicMock()
    list_scope.list_entries.return_value = [("./foo.txt", False)]
    list_scope.scope_label.return_value = "."
    action_menu = MagicMock()
    mode = BrowseMode(console, MagicMock(), list_scope, action_menu)
    mode.run(".", ".\nfoo.txt", MagicMock())
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_run_empty_input_cancels(capsys):
    mode = make_browse_mode(inputs=[""])
    mode.run(".", ".\nfoo.txt\nreports", MagicMock())
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_run_numeric_input_calls_action_menu(capsys):
    mode = make_browse_mode(inputs=["1"])
    mode.action_menu.show = MagicMock()
    mode.run(".", ".\nfoo.txt\nreports", MagicMock())
    mode.action_menu.show.assert_called_once()


def test_run_typed_no_match_shows_notice(capsys):
    mode = make_browse_mode(inputs=["zzznomatch", ""])
    mode.run(".", ".\nfoo.txt\nreports", MagicMock())
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_run_dry_run_mode_prints_and_returns(capsys):
    console = MagicMock()
    console.yes = False
    console.dry_run = True
    console.abs_path.side_effect = lambda p: f"/abs/{p}"
    console.cwd_label.return_value = "/cwd  (Current directory)"
    console.render_menu.return_value = "menu"
    list_scope = MagicMock()
    list_scope.list_entries.return_value = [("./foo.txt", False)]
    list_scope.scope_label.return_value = "."
    action_menu = MagicMock()
    mode = BrowseMode(console, MagicMock(), list_scope, action_menu)
    mode.run(".", ".\nfoo.txt", MagicMock())
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_run_typed_single_dir_navigates():
    mode = make_browse_mode(inputs=["reports", ""])
    mode.list_scope.list_entries.side_effect = [
        [("./foo.txt", False), ("./reports", True)],
        [("./reports/bar.txt", False)],
    ]
    mode.list_scope.scoped_context.return_value = ".\nreports"
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", return_value=["./reports"]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", return_value=[]):
            mode.run(".", ".\nfoo.txt\nreports", MagicMock())


def test_run_typed_multiple_dirs_disambiguate_cancelled(capsys):
    from mash.helpers.selection.disambiguator import Selection
    mode = make_browse_mode(inputs=["rep"])
    mode.disambiguator.pick_from_hits.return_value = Selection(kind="cancelled", value="")
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", return_value=["./reports", "./repo"]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", return_value=[]):
            mode.run(".", ".\nfoo.txt\nreports\nrepo", MagicMock())
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_run_typed_multiple_dirs_disambiguate_typed_single_dir():
    from mash.helpers.selection.disambiguator import Selection
    mode = make_browse_mode(inputs=["rep", ""])
    mode.disambiguator.pick_from_hits.return_value = Selection(kind="typed", value="reports")
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", side_effect=[
        ["./reports", "./repo"],  # initial typed search
        ["./reports"],            # re-resolve after typed selection
    ]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", return_value=[]):
            mode.run(".", ".\nfoo.txt\nreports\nrepo", MagicMock())


def test_run_typed_multiple_dirs_disambiguate_typed_single_file():
    from mash.helpers.selection.disambiguator import Selection
    mode = make_browse_mode(inputs=["rep", ""])
    mode.disambiguator.pick_from_hits.return_value = Selection(kind="typed", value="foo.txt")
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", side_effect=[
        ["./reports", "./repo"],  # initial typed search dirs
        [],                       # re-resolve dirs (none)
    ]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", side_effect=[
            [],                   # initial typed search files
            ["./foo.txt"],        # re-resolve files
        ]):
            with patch("os.path.isdir", return_value=False):
                mode.run(".", ".\nfoo.txt\nreports\nrepo", MagicMock())


def test_run_typed_multiple_dirs_disambiguate_typed_notice():
    from mash.helpers.selection.disambiguator import Selection
    mode = make_browse_mode(inputs=["rep", ""])
    mode.disambiguator.pick_from_hits.return_value = Selection(kind="typed", value="zzznomatch")
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", side_effect=[
        ["./reports", "./repo"],  # initial
        [],                       # re-resolve
    ]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", side_effect=[
            [],   # initial files
            [],   # re-resolve files
        ]):
            mode.run(".", ".\nreports\nrepo", MagicMock())


def test_run_typed_multiple_dirs_disambiguate_selected():
    from mash.helpers.selection.disambiguator import Selection
    mode = make_browse_mode(inputs=["rep", ""])
    mode.disambiguator.pick_from_hits.return_value = Selection(kind="selected", value="./reports")
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", return_value=["./reports", "./repo"]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", return_value=[]):
            mode.run(".", ".\nreports\nrepo", MagicMock())


def test_run_typed_single_file_narrows():
    mode = make_browse_mode(inputs=["foo", ""])
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", return_value=[]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", return_value=["./foo.txt"]):
            with patch("os.path.isdir", return_value=False):
                mode.run(".", ".\nfoo.txt\nreports", MagicMock())


def test_run_typed_multiple_files_disambiguate_cancelled(capsys):
    from mash.helpers.selection.disambiguator import Selection
    mode = make_browse_mode(inputs=["f"])
    mode.disambiguator.pick_from_hits.return_value = Selection(kind="cancelled", value="")
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", return_value=[]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", return_value=["./foo.txt", "./fig.txt"]):
            mode.run(".", ".\nfoo.txt\nfig.txt", MagicMock())
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_run_typed_multiple_files_disambiguate_typed_single_file():
    from mash.helpers.selection.disambiguator import Selection
    mode = make_browse_mode(inputs=["f", ""])
    mode.disambiguator.pick_from_hits.return_value = Selection(kind="typed", value="foo.txt")
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", side_effect=[[], []]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", side_effect=[
            ["./foo.txt", "./fig.txt"],
            ["./foo.txt"],
        ]):
            with patch("os.path.isdir", return_value=False):
                mode.run(".", ".\nfoo.txt\nfig.txt", MagicMock())


def test_run_typed_multiple_files_disambiguate_typed_single_dir():
    from mash.helpers.selection.disambiguator import Selection
    mode = make_browse_mode(inputs=["f", ""])
    mode.disambiguator.pick_from_hits.return_value = Selection(kind="typed", value="reports")
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", side_effect=[[], ["./reports"]]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", side_effect=[
            ["./foo.txt", "./fig.txt"],
            [],
        ]):
            mode.run(".", ".\nfoo.txt\nfig.txt\nreports", MagicMock())


def test_run_typed_multiple_files_disambiguate_typed_notice():
    from mash.helpers.selection.disambiguator import Selection
    mode = make_browse_mode(inputs=["f", ""])
    mode.disambiguator.pick_from_hits.return_value = Selection(kind="typed", value="zzz")
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", side_effect=[[], []]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", side_effect=[
            ["./foo.txt", "./fig.txt"],
            [],
        ]):
            mode.run(".", ".\nfoo.txt\nfig.txt", MagicMock())


def test_run_typed_multiple_files_disambiguate_selected():
    from mash.helpers.selection.disambiguator import Selection
    mode = make_browse_mode(inputs=["f", ""])
    mode.disambiguator.pick_from_hits.return_value = Selection(kind="selected", value="./foo.txt")
    from unittest.mock import patch
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", return_value=[]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", return_value=["./foo.txt", "./fig.txt"]):
            with patch("os.path.isdir", return_value=False):
                mode.run(".", ".\nfoo.txt\nfig.txt", MagicMock())


def test_run_non_numeric_scope_label_differs_from_cwd():
    mode = make_browse_mode(inputs=["1"])
    mode.list_scope.scope_label.return_value = "./reports"
    mode.list_scope.list_entries.return_value = [("./reports/a.txt", False)]
    mode.run("./reports", ".\nreports\na.txt", MagicMock())
    mode.action_menu.show.assert_called_once()


def test_run_out_of_range_int_triggers_value_error(capsys):
    mode = make_browse_mode(inputs=["99", ""])
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", return_value=[]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", return_value=[]):
            mode.run(".", ".\nfoo.txt\nreports", MagicMock())
    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_run_linear_search_finds_dir_and_file(capsys):
    mode = make_browse_mode(inputs=["o", ""])
    with patch("mash.flows.browse_mode.PathResolver.resolve_dirs", return_value=[]):
        with patch("mash.flows.browse_mode.PathResolver.resolve_paths", return_value=[]):
            mode.run(".", ".\nfoo.txt\nreports", MagicMock())
    out = capsys.readouterr().out
    assert "Cancelled." in out
