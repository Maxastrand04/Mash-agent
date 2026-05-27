from mash.helpers.commands.command_reference import CommandReference


def test_commands_list_is_non_empty_string():
    assert isinstance(CommandReference.COMMANDS_LIST, str)
    assert len(CommandReference.COMMANDS_LIST) > 0


def test_commands_list_contains_mv():
    assert "mv" in CommandReference.COMMANDS_LIST


def test_commands_dict_is_class_attribute():
    assert isinstance(CommandReference.COMMANDS, dict)
    assert "ls" in CommandReference.COMMANDS


def test_commands_list_contains_all_keys():
    for key in CommandReference.COMMANDS:
        assert key in CommandReference.COMMANDS_LIST
