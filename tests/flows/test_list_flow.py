import pytest
from unittest.mock import MagicMock
from mash.flows.list_flow import ListFlow
from mash.intent import Intent
from mash.exceptions import UserCancelled


def make_list_flow(dry_run=True):
    console = MagicMock()
    console.yes = True
    console.dry_run = dry_run
    disambiguator = MagicMock()
    list_scope = MagicMock()
    list_scope.list_target_from_arguments.return_value = "."
    list_scope.scope_label.return_value = "."
    action_menu = MagicMock()
    browse_mode = MagicMock()
    run_with_args = MagicMock()
    return ListFlow(
        console, disambiguator, browse_mode, action_menu,
        list_scope, run_with_args, ".\nfoo.txt"
    )


def test_run_dry_run_calls_confirm_and_run():
    flow = make_list_flow(dry_run=True)
    intent = Intent.parse(["ls"])
    flow.run(intent)
    flow.console.confirm_and_run.assert_called_once()


def test_run_non_dry_run_calls_browse_mode():
    flow = make_list_flow(dry_run=False)
    intent = Intent.parse(["ls"])
    flow.run(intent)
    flow.browse_mode.run.assert_called_once()


def test_run_browse_mode_cancelled_calls_print_info():
    flow = make_list_flow(dry_run=False)
    flow.browse_mode.run.side_effect = UserCancelled()
    intent = Intent.parse(["ls"])
    flow.run(intent)
    flow.console.print_info.assert_called_with("Cancelled.")
