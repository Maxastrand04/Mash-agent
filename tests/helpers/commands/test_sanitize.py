from mash.helpers.commands.sanitize import (
    normalize_template_verb,
    apply_source,
    apply_destination,
    apply_rename,
    apply_filename,
    strip_recursive_flags,
)


def test_normalize_template_verb_known_label():
    assert normalize_template_verb("move_file foo bar") == "mv foo bar"


def test_normalize_template_verb_create_folder():
    assert normalize_template_verb("create_folder x") == "mkdir -p x"


def test_normalize_template_verb_passthrough():
    assert normalize_template_verb("mv a b") == "mv a b"


def test_apply_source_already_present_noop():
    cmd = "mv ./x dir/"
    assert apply_source(cmd, "./x") == cmd


def test_apply_source_mv_replaces_first_positional():
    out = apply_source("mv old new", "./x")
    assert out == "mv ./x new"


def test_apply_source_rm_replaces_last():
    out = apply_source("rm -rf placeholder", "./real")
    assert out == "rm -rf ./real"


def test_apply_destination_simple():
    out = apply_destination("mv a b", "dir")
    assert out == "mv a dir/"


def test_apply_destination_with_chained_command():
    out = apply_destination("mkdir -p d && mv a b", "dir")
    assert out.endswith("mv a dir/")
    assert out.startswith("mkdir -p d &&")


def test_apply_destination_non_mv_cp_noop():
    cmd = "rm -rf foo"
    assert apply_destination(cmd, "dir") == cmd


def test_apply_rename_no_destination_root():
    out = apply_rename("mv foo bar", "foo", "bar")
    assert out == "mv foo ./bar"


def test_apply_rename_preserves_parent_dir():
    out = apply_rename("mv sub/old placeholder", "sub/old", "new")
    assert out == "mv sub/old sub/new"


def test_apply_rename_with_destination():
    out = apply_rename("mv foo placeholder", "foo", "bar", destination="dest")
    assert out == "mv foo dest/bar"


def test_apply_filename_with_destination():
    out = apply_filename("touch ./my report.py", "my report", "my_report.py", destination="dest")
    assert "dest/my_report.py" in out


def test_apply_filename_touch_fallback():
    out = apply_filename("touch placeholder", "my report", "my_report.py")
    assert out == "touch ./my_report.py"


def test_strip_recursive_flags_file_strips_rf_and_r():
    assert strip_recursive_flags("rm -rf x", "file") == "rm x"
    assert strip_recursive_flags("cp -r a b", "file") == "cp a b"


def test_strip_recursive_flags_folder_keeps_flags():
    assert strip_recursive_flags("rm -rf x", "folder") == "rm -rf x"
    assert strip_recursive_flags("cp -r a b", "folder") == "cp -r a b"
