from mash.helpers.commands.command_templates import CommandTemplates


def test_templates_list_is_non_empty_string():
    assert isinstance(CommandTemplates.TEMPLATES_LIST, str)
    assert len(CommandTemplates.TEMPLATES_LIST) > 0


def test_templates_list_contains_move():
    assert "move_file" in CommandTemplates.TEMPLATES_LIST


def test_templates_list_contains_create_folder():
    assert "create_folder" in CommandTemplates.TEMPLATES_LIST


def test_templates_dict_is_class_attribute():
    assert isinstance(CommandTemplates.TEMPLATES, dict)
    assert "rename" in CommandTemplates.TEMPLATES


def test_templates_list_is_string_of_templates():
    for key in CommandTemplates.TEMPLATES:
        assert key in CommandTemplates.TEMPLATES_LIST
