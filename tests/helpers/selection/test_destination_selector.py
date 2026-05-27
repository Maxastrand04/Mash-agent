import pytest
from unittest.mock import MagicMock, patch
from mash.helpers.selection.destination_selector import DestinationSelector
from mash.helpers.selection.disambiguator import Selection
from mash.exceptions import UserCancelled, DestinationNotFound


FAKE_CONTEXT = ".\nreports\narchive"


def make_console(yes=True, dry_run=False):
    c = MagicMock()
    c.yes = yes
    c.dry_run = dry_run
    c.cwd_label.return_value = "/cwd  (Current directory)"
    c.abs_path.side_effect = lambda p: f"/abs/{p}"
    return c


def test_select_yes_with_candidates_returns_first(capsys):
    console = make_console(yes=True)
    selector = DestinationSelector(console, MagicMock())
    dest, create = selector.select(["reports"], FAKE_CONTEXT, destination_token="reports")
    assert dest == "reports"
    assert create is False


def test_select_yes_no_real_candidates_no_token_raises(capsys):
    console = make_console(yes=True)
    selector = DestinationSelector(console, MagicMock())
    with pytest.raises(DestinationNotFound):
        selector.select([], FAKE_CONTEXT, destination_token=None, for_create=False)


def test_select_yes_for_create_no_candidates_returns_dot(capsys):
    console = make_console(yes=True)
    selector = DestinationSelector(console, MagicMock())
    dest, create = selector.select([], FAKE_CONTEXT, destination_token=None, for_create=True)
    assert dest == "."
    assert create is False


def test_select_dry_run_with_candidates(capsys):
    console = make_console(yes=False, dry_run=True)
    selector = DestinationSelector(console, MagicMock())
    dest, create = selector.select(["reports"], FAKE_CONTEXT, destination_token="reports")
    assert dest == "reports"


def test_select_interactive_selected_path():
    console = make_console(yes=False)
    d = MagicMock()
    d.pick_with_actions.return_value = Selection(kind="selected", value="reports")
    selector = DestinationSelector(console, d)
    dest, create = selector.select(
        ["reports"], FAKE_CONTEXT, destination_token="reports"
    )
    assert dest == "reports"
    assert create is False


def test_select_interactive_cancel_raises():
    console = make_console(yes=False)
    d = MagicMock()
    d.pick_from_hits.side_effect = UserCancelled()
    d.pick_with_actions.side_effect = UserCancelled()
    selector = DestinationSelector(console, d)
    with pytest.raises(UserCancelled):
        selector.select(["reports"], FAKE_CONTEXT, destination_token="reports")


def test_select_yes_for_create_with_token_no_real_returns_path(capsys):
    console = make_console(yes=True)
    selector = DestinationSelector(console, MagicMock())
    dest, create = selector.select(
        [], FAKE_CONTEXT, destination_token="newdir", for_create=True
    )
    assert "newdir" in dest
    assert create is True


def test_select_interactive_no_dest_select_cwd():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.return_value = Selection(kind="action", value="select_cwd")
    selector = DestinationSelector(console, d)
    dest, create = selector.select([], FAKE_CONTEXT, destination_token=None, for_create=False)
    assert dest == "."
    assert create is False


def test_select_interactive_no_dest_typed_then_found():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="reports"),   # no_destination_given → typed answer
        Selection(kind="selected", value="reports"), # real candidates → selected
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=["reports"]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token=None, for_create=False)
    assert dest == "reports"


def test_select_interactive_no_dest_typed_not_found_loops():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="nowhere"),
        Selection(kind="action", value="select_cwd"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=[]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token=None, for_create=False)
    assert dest == "."


def test_select_interactive_for_create_no_token_select_cwd():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.return_value = Selection(kind="action", value="select_cwd")
    selector = DestinationSelector(console, d)
    dest, create = selector.select([], FAKE_CONTEXT, destination_token=None, for_create=True)
    assert dest == "."
    assert create is False


def test_select_interactive_for_create_no_token_typed():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="reports"),
        Selection(kind="selected", value="reports"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=["reports"]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token=None, for_create=True)
    assert dest == "reports"
    assert create is False


def test_select_interactive_for_create_token_not_found_select_cwd():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.return_value = Selection(kind="action", value="select_cwd")
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=[]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token="newdir", for_create=True)
    assert dest == "."
    assert create is False


def test_select_interactive_for_create_token_not_found_create_here():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.return_value = Selection(kind="action", value="create_here")
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=[]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token="newdir", for_create=True)
    assert "newdir" in dest
    assert create is True


def test_select_interactive_for_create_token_not_found_typed():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="reports"),    # token not found → typed answer
        Selection(kind="selected", value="reports"), # real candidates found → selected
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=["reports"]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token="newdir", for_create=True)
    assert dest == "reports"


def test_select_interactive_for_create_real_candidates_selected():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.return_value = Selection(kind="selected", value="reports")
    selector = DestinationSelector(console, d)
    dest, create = selector.select(["reports"], FAKE_CONTEXT, destination_token="reports", for_create=True)
    assert dest == "reports"
    assert create is False


def test_select_interactive_for_create_real_typed_resolves():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="archive"),
        Selection(kind="selected", value="archive"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=["archive"]):
        dest, create = selector.select(["reports"], FAKE_CONTEXT, destination_token="reports", for_create=True)
    assert dest == "archive"


def test_select_interactive_for_create_real_typed_not_resolved():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="nowhere"),
        Selection(kind="action", value="select_cwd"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=[]):
        dest, create = selector.select(["reports"], FAKE_CONTEXT, destination_token="reports", for_create=True)
    assert dest == "."
    assert create is False


def test_select_interactive_not_for_create_no_real_create_here():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.return_value = Selection(kind="action", value="create_here")
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=[]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token="mydir", for_create=False)
    assert "mydir" in dest
    assert create is True


def test_select_interactive_not_for_create_no_real_select_cwd():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.return_value = Selection(kind="action", value="select_cwd")
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=[]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token="mydir", for_create=False)
    assert dest == "."


def test_select_interactive_not_for_create_no_real_typed_found():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="reports"),
        Selection(kind="action", value="select_cwd"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               side_effect=[[], ["reports"], []]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token="mydir", for_create=False)


def test_select_interactive_not_for_create_no_real_typed_not_found():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="nowhere"),
        Selection(kind="action", value="select_cwd"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=[]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token="mydir", for_create=False)


def test_select_interactive_not_for_create_real_selected():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.return_value = Selection(kind="selected", value="reports")
    selector = DestinationSelector(console, d)
    dest, create = selector.select(["reports"], FAKE_CONTEXT, destination_token="reports", for_create=False)
    assert dest == "reports"
    assert create is False


def test_select_interactive_not_for_create_real_typed_found():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="archive"),
        Selection(kind="selected", value="archive"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=["archive"]):
        dest, create = selector.select(["reports"], FAKE_CONTEXT, destination_token="reports", for_create=False)
    assert dest == "archive"


def test_select_interactive_not_for_create_real_typed_not_found():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="nowhere"),
        Selection(kind="action", value="select_cwd"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=[]):
        dest, create = selector.select(["reports"], FAKE_CONTEXT, destination_token="reports", for_create=False)
    assert dest == "."


def test_select_yes_candidates_already_has_dot():
    console = make_console(yes=True)
    selector = DestinationSelector(console, MagicMock())
    dest, create = selector.select(["reports", "."], FAKE_CONTEXT, destination_token="reports")
    assert dest == "reports"
    assert create is False


def test_select_interactive_for_create_no_token_typed_not_found_then_cwd():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="nowhere"),
        Selection(kind="action", value="select_cwd"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=[]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token=None, for_create=True)
    assert dest == "."
    assert create is False


def test_select_interactive_for_create_unknown_action_falls_through():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="action", value="unknown_action"),
        Selection(kind="action", value="select_cwd"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=[]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token="newdir", for_create=True)
    assert dest == "."
    assert create is False


def test_select_interactive_not_for_create_unknown_action_falls_through():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="action", value="unknown_action"),
        Selection(kind="action", value="select_cwd"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=[]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token="mydir", for_create=False)
    assert dest == "."


def test_select_interactive_not_for_create_no_real_typed_found_updates_candidates():
    console = make_console(yes=False)
    from mash.helpers.selection.disambiguator import Selection
    d = MagicMock()
    d.pick_with_actions.side_effect = [
        Selection(kind="typed", value="reports"),
        Selection(kind="selected", value="reports"),
    ]
    selector = DestinationSelector(console, d)
    with patch("mash.helpers.selection.destination_selector.PathResolver.resolve_dirs",
               return_value=["reports"]):
        dest, create = selector.select([], FAKE_CONTEXT, destination_token="mydir", for_create=False)
    assert dest == "reports"
    assert create is False
