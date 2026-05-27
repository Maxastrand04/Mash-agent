import pytest
from mash.intent import Intent


def test_parse_cat_verb():
    i = Intent.parse(["cat", "foo.txt"])
    assert i.verb == "cat"


def test_parse_show_contents_of_is_cat():
    i = Intent.parse(["show", "contents", "of", "foo.txt"])
    assert i.verb == "cat"


def test_parse_print_is_cat():
    i = Intent.parse(["print", "foo.txt"])
    assert i.verb == "cat"


def test_parse_list_ls():
    i = Intent.parse(["ls"])
    assert i.verb == "list"


def test_parse_list_show_files():
    i = Intent.parse(["show", "files"])
    assert i.verb == "list"


def test_parse_open():
    i = Intent.parse(["open", "foo.txt"])
    assert i.verb == "open"


def test_parse_delete():
    assert Intent.parse(["delete", "foo"]).verb == "delete"


def test_parse_remove():
    assert Intent.parse(["remove", "foo"]).verb == "delete"


def test_parse_move():
    i = Intent.parse(["move", "a", "to", "b"])
    assert i.verb == "move"
    assert i.dest_token == "b"


def test_parse_copy_synonyms():
    for verb in ("copy", "duplicate", "clone", "replicate"):
        assert Intent.parse([verb, "a", "to", "b"]).verb == "copy"


def test_parse_rename_simple():
    i = Intent.parse(["rename", "foo", "to", "bar"])
    assert i.verb == "rename"
    assert i.rename_target == "bar"


def test_parse_rename_with_destination():
    i = Intent.parse(["move", "foo", "to", "dir", "and", "rename", "to", "bar"])
    assert i.verb == "rename"
    assert i.rename_target == "bar"
    assert i.dest_token == "dir"


def test_parse_destination_with_article():
    i = Intent.parse(["move", "a", "into", "the", "newdir"])
    assert i.dest_token == "newdir"


def test_parse_create_file_explicit_word():
    i = Intent.parse(["create", "file", "foo.py"])
    assert i.verb == "create"
    assert i.is_create_file is True
    assert i.is_create_folder is False


def test_parse_create_folder_explicit_word():
    i = Intent.parse(["create", "folder", "mydir"])
    assert i.verb == "create"
    assert i.is_create_folder is True
    assert i.is_create_file is False


def test_parse_create_directory_word():
    i = Intent.parse(["create", "directory", "mydir"])
    assert i.verb == "create"
    assert i.is_create_folder is True


def test_parse_create_bare_filename_pattern():
    i = Intent.parse(["create", "foo.py"])
    assert i.verb == "create"
    assert i.is_create_file is True


def test_parse_create_named_marker_extracts_name():
    i = Intent.parse(["create", "file", "named", "my", "report.md"])
    assert i.verb == "create"
    assert "named" not in i.filtered_args
    assert "my" not in i.filtered_args
    assert "report.md" not in i.filtered_args


def test_parse_create_named_with_extension_keyword():
    i = Intent.parse(["create", "file", "named", "my", "report", "markdown"])
    assert i.verb == "create"
    assert i.is_create_file is True


def test_parse_filtered_args_drops_destination_token():
    i = Intent.parse(["move", "a", "to", "b"])
    assert "b" not in i.filtered_args
    assert "a" in i.filtered_args


def test_parse_other_verb_fallback():
    i = Intent.parse(["frobnicate", "things"])
    assert i.verb == "other"


def test_parse_empty_args():
    i = Intent.parse([])
    assert i.verb == "other"
    assert i.dest_token is None


def test_parse_make_form():
    i = Intent.parse(["make", "folder", "stuff"])
    assert i.verb == "create"
    assert i.is_create_folder is True


def test_class_attribute_stop_words():
    assert "move" in Intent._STOP_WORDS
    assert "to" in Intent._STOP_WORDS


def test_class_attribute_rename_verbs():
    assert "rename" in Intent._RENAME_VERBS


def test_class_attribute_list_triggers():
    assert "ls" in Intent._LIST_TRIGGERS
    assert "list" in Intent._LIST_TRIGGERS


def test_class_attribute_open_triggers():
    assert "open" in Intent._OPEN_TRIGGERS


def test_class_attribute_cat_triggers():
    assert "cat" in Intent._CAT_TRIGGERS
    assert "print" in Intent._CAT_TRIGGERS


def test_looks_like_filename_with_extension():
    assert Intent._looks_like_filename("foo.txt") is True
    assert Intent._looks_like_filename("foo") is False
    assert Intent._looks_like_filename("foo.bar.baz") is False


def test_detect_new_filename_none_when_not_create_form():
    result = Intent._detect_new_filename(["move", "foo", "to", "bar"])
    assert result is None


def test_detect_new_filename_none_when_no_marker():
    result = Intent._detect_new_filename(["create", "foo.py"])
    assert result is None


def test_detect_new_filename_with_marker():
    result = Intent._detect_new_filename(["create", "file", "named", "my", "report.md"])
    assert result is not None
    raw_name, extension = result
    assert raw_name == "my report"
    assert extension == ".md"


def test_detect_destination_idx_into_marker():
    i = Intent.parse(["move", "foo", "into", "bar"])
    assert i.dest_token == "bar"


def test_detect_destination_idx_inside_marker():
    i = Intent.parse(["move", "foo", "inside", "bar"])
    assert i.dest_token == "bar"


def test_rename_without_to_returns_none_target():
    i = Intent.parse(["rename", "foo"])
    assert i.verb == "rename"
    assert i.rename_target is None


def test_create_bare_no_filename_no_folder_no_file_is_create():
    i = Intent.parse(["create", "something"])
    assert i.verb == "create"


def test_parse_args_stored():
    i = Intent.parse(["move", "a", "to", "b"])
    assert i.args == ["move", "a", "to", "b"]


def test_find_rename_verb_start_prefers_latest_match():
    # "rename" at index 2 should win over "change name" at index 0
    result = Intent._find_rename_verb_start(["change", "name", "rename", "to", "foo"])
    assert result == 2


def test_extract_rename_target_none_when_rename_verb_only_substring():
    # "something-renamed" contains "rename" as a substring but not as a token
    i = Intent.parse(["something-renamed", "to", "bar"])
    assert i.rename_target is None


def test_detect_destination_idx_marker_at_end_returns_none():
    i = Intent.parse(["move", "foo", "to"])
    assert i.dest_token is None


def test_detect_destination_idx_before_rename_falls_back_when_no_rename_start():
    # "something-renamed" triggers _detect_rename_intent (substring match) but
    # _find_rename_verb_start returns None (no standalone token), so falls back to
    # _detect_destination_idx which finds "to" at index 1 → destination at index 2
    result = Intent._detect_destination_idx_before_rename(["something-renamed", "to", "bar"])
    assert result == 2


def test_detect_destination_idx_before_rename_no_marker_before_rename():
    result = Intent._detect_destination_idx_before_rename(["foo", "rename", "to", "bar"])
    assert result is None


def test_detect_destination_idx_before_rename_with_article():
    result = Intent._detect_destination_idx_before_rename(
        ["move", "to", "the", "reports", "rename", "to", "bar"]
    )
    assert result == 3


def test_detect_destination_idx_before_rename_marker_at_boundary():
    # "to" marker but the destination index equals rename_start → False branch of j < rename_start
    result = Intent._detect_destination_idx_before_rename(
        ["move", "to", "rename", "to", "bar"]
    )
    assert result is None


def test_detect_new_filename_no_dot_tokens_checks_extension_map():
    result = Intent._detect_new_filename(["create", "file", "called", "my", "report", "python"])
    assert result is not None
    raw_name, extension = result
    # "my", "report", "python" all go into name_tokens (no dots); extension found from EXTENSION_MAP
    assert "my" in raw_name
    assert extension == ".py"


def test_detect_new_filename_single_token_returns_none():
    result = Intent._detect_new_filename(["create", "file", "called", "report"])
    assert result is None


def test_detect_new_filename_no_dot_no_extension_map():
    result = Intent._detect_new_filename(["create", "file", "called", "my", "thing"])
    assert result is not None
    raw_name, extension = result
    assert raw_name == "my thing"
    assert extension == ""
