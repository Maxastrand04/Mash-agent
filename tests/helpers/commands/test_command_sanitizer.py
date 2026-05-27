import pytest
from mash.helpers.commands.command_sanitizer import CommandSanitizer


def test_normalize_template_verb_known_label():
    assert CommandSanitizer.normalize_template_verb("move_file foo bar") == "mv foo bar"


def test_normalize_template_verb_create_folder():
    assert CommandSanitizer.normalize_template_verb("create_folder x") == "mkdir -p x"


def test_normalize_template_verb_delete_file():
    assert CommandSanitizer.normalize_template_verb("delete_file x") == "rm x"


def test_normalize_template_verb_delete_folder():
    assert CommandSanitizer.normalize_template_verb("delete_folder x") == "rm -rf x"


def test_normalize_template_verb_copy_folder():
    assert CommandSanitizer.normalize_template_verb("copy_folder a b") == "cp -r a b"


def test_normalize_template_verb_passthrough():
    assert CommandSanitizer.normalize_template_verb("mv a b") == "mv a b"


def test_normalize_template_verb_unknown_passthrough():
    assert CommandSanitizer.normalize_template_verb("frobnicate x") == "frobnicate x"


def test_apply_source_already_present_noop():
    cmd = "mv ./x dir/"
    assert CommandSanitizer.apply_source(cmd, "./x") == cmd


def test_apply_source_mv_replaces_first_positional():
    out = CommandSanitizer.apply_source("mv old new", "./x")
    assert out == "mv ./x new"


def test_apply_source_cp_replaces_first_positional():
    out = CommandSanitizer.apply_source("cp old new", "./x")
    assert out == "cp ./x new"


def test_apply_source_rm_replaces_last():
    out = CommandSanitizer.apply_source("rm -rf placeholder", "./real")
    assert out == "rm -rf ./real"


def test_apply_source_empty_command():
    assert CommandSanitizer.apply_source("", "./x") == ""


def test_apply_destination_simple():
    out = CommandSanitizer.apply_destination("mv a b", "dir")
    assert out == "mv a dir/"


def test_apply_destination_with_chained_command():
    out = CommandSanitizer.apply_destination("mkdir -p d && mv a b", "dir")
    assert out.endswith("mv a dir/")
    assert out.startswith("mkdir -p d &&")


def test_apply_destination_non_mv_cp_noop():
    cmd = "rm -rf foo"
    assert CommandSanitizer.apply_destination(cmd, "dir") == cmd


def test_apply_destination_cp():
    out = CommandSanitizer.apply_destination("cp a b", "destdir")
    assert out == "cp a destdir/"


def test_apply_rename_no_destination_root():
    out = CommandSanitizer.apply_rename("mv foo bar", "foo", "bar")
    assert out == "mv foo ./bar"


def test_apply_rename_preserves_parent_dir():
    out = CommandSanitizer.apply_rename("mv sub/old placeholder", "sub/old", "new")
    assert out == "mv sub/old sub/new"


def test_apply_rename_with_destination():
    out = CommandSanitizer.apply_rename("mv foo placeholder", "foo", "bar", destination="dest")
    assert out == "mv foo dest/bar"


def test_apply_rename_non_mv_passthrough():
    cmd = "cp a b"
    assert CommandSanitizer.apply_rename(cmd, "a", "c") == cmd


def test_apply_rename_after_with_slash():
    out = CommandSanitizer.apply_rename("mv foo bar", "foo", "sub/new.txt")
    assert "sub/new.txt" in out


def test_apply_filename_with_destination():
    out = CommandSanitizer.apply_filename("touch ./my report.py", "my report", "my_report.py", destination="dest")
    assert "dest/my_report.py" in out


def test_apply_filename_touch_fallback():
    out = CommandSanitizer.apply_filename("touch placeholder", "my report", "my_report.py")
    assert out == "touch ./my_report.py"


def test_apply_filename_mkdir_fallback():
    out = CommandSanitizer.apply_filename("mkdir -p placeholder", "my dir", "my_dir")
    assert "my_dir" in out


def test_strip_recursive_flags_file_strips_rf_and_r():
    assert CommandSanitizer.strip_recursive_flags("rm -rf x", "file") == "rm x"
    assert CommandSanitizer.strip_recursive_flags("cp -r a b", "file") == "cp a b"


def test_strip_recursive_flags_folder_keeps_flags():
    assert CommandSanitizer.strip_recursive_flags("rm -rf x", "folder") == "rm -rf x"
    assert CommandSanitizer.strip_recursive_flags("cp -r a b", "folder") == "cp -r a b"


def test_strip_recursive_flags_unknown_strips():
    assert CommandSanitizer.strip_recursive_flags("rm -rf x", "unknown") == "rm x"


def test_label_to_shell_command_is_class_attribute():
    assert isinstance(CommandSanitizer._LABEL_TO_SHELL_COMMAND, dict)
    assert CommandSanitizer._LABEL_TO_SHELL_COMMAND["move_file"] == "mv"


def test_apply_source_unknown_verb_returns_command():
    cmd = "open ./foo.txt"
    assert CommandSanitizer.apply_source(cmd, "./bar.txt") == cmd


def test_apply_source_mv_with_flag_before_positional():
    out = CommandSanitizer.apply_source("mv -v old new", "./x")
    assert "./x" in out


def test_apply_destination_chained_non_mv_cp_last_segment():
    cmd = "mkdir -p foo && chmod 755 foo"
    result = CommandSanitizer.apply_destination(cmd, "bar")
    assert result == cmd


def test_apply_rename_flag_before_source():
    out = CommandSanitizer.apply_rename("mv -v old new", "old", "renamed")
    assert "old" in out


def test_apply_filename_no_match_and_not_touch_mkdir():
    cmd = "open ./differentfile"
    result = CommandSanitizer.apply_filename(cmd, "myfile", "my_file.txt")
    assert result == cmd


def test_apply_source_all_flags_no_positional_returns_command():
    out = CommandSanitizer.apply_source("mv -v", "./x")
    assert out == "mv -v"


def test_apply_rename_all_flags_no_positional_still_renames_last():
    out = CommandSanitizer.apply_rename("mv -v", "old", "new")
    assert "new" in out
