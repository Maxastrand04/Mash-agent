from mash.intent import parse_intent


def test_parse_cat_verb():
    i = parse_intent(["cat", "foo.txt"])
    assert i.verb == "cat"


def test_parse_show_contents_of_is_cat():
    i = parse_intent(["show", "contents", "of", "foo.txt"])
    assert i.verb == "cat"


def test_parse_list_ls():
    i = parse_intent(["ls"])
    assert i.verb == "list"


def test_parse_list_show_files():
    i = parse_intent(["show", "files"])
    assert i.verb == "list"


def test_parse_open():
    i = parse_intent(["open", "foo.txt"])
    assert i.verb == "open"


def test_parse_delete():
    assert parse_intent(["delete", "foo"]).verb == "delete"


def test_parse_remove():
    assert parse_intent(["remove", "foo"]).verb == "delete"


def test_parse_move():
    i = parse_intent(["move", "a", "to", "b"])
    assert i.verb == "move"
    assert i.dest_token == "b"


def test_parse_copy_synonyms():
    for verb in ("copy", "duplicate", "clone", "replicate"):
        assert parse_intent([verb, "a", "to", "b"]).verb == "copy"


def test_parse_rename_simple():
    i = parse_intent(["rename", "foo", "to", "bar"])
    assert i.verb == "rename"
    assert i.rename_target == "bar"


def test_parse_rename_with_destination():
    i = parse_intent(["move", "foo", "to", "dir", "and", "rename", "to", "bar"])
    assert i.verb == "rename"
    assert i.rename_target == "bar"
    assert i.dest_token == "dir"


def test_parse_destination_with_article():
    i = parse_intent(["move", "a", "into", "the", "newdir"])
    assert i.dest_token == "newdir"


def test_parse_create_file_explicit_word():
    i = parse_intent(["create", "file", "foo.py"])
    assert i.verb == "create"
    assert i.is_create_file is True
    assert i.is_create_folder is False


def test_parse_create_folder_explicit_word():
    i = parse_intent(["create", "folder", "mydir"])
    assert i.verb == "create"
    assert i.is_create_folder is True
    assert i.is_create_file is False


def test_parse_create_bare_filename_pattern():
    i = parse_intent(["create", "foo.py"])
    assert i.verb == "create"
    assert i.is_create_file is True


def test_parse_create_named_marker_extracts_name():
    # The "called/named" branch is asserted by the filtered_args truncation:
    # everything from "named" onward is dropped from filtered_args.
    i = parse_intent(["create", "file", "named", "my", "report.md"])
    assert i.verb == "create"
    assert "named" not in i.filtered_args
    assert "my" not in i.filtered_args
    assert "report.md" not in i.filtered_args


def test_parse_create_named_with_extension_keyword():
    i = parse_intent(["create", "file", "named", "my", "report", "markdown"])
    assert i.verb == "create"
    assert i.is_create_file is True


def test_parse_filtered_args_drops_destination_token():
    i = parse_intent(["move", "a", "to", "b"])
    assert "b" not in i.filtered_args
    assert "a" in i.filtered_args


def test_parse_other_verb_fallback():
    i = parse_intent(["frobnicate", "things"])
    assert i.verb == "other"


def test_parse_empty_args():
    i = parse_intent([])
    assert i.verb == "other"
    assert i.dest_token is None
