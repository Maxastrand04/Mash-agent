import pytest
import textwrap
from pathlib import Path
from mash.exceptions import MashError
from scripts.check_conventions import ConventionChecker


def write_py(tmp_path, name, source):
    p = tmp_path / name
    p.write_text(textwrap.dedent(source))
    return str(p)


def test_no_module_level_def_clean():
    checker = ConventionChecker()
    violations = checker.check_no_module_level_def(
        str(Path(__file__).parent.parent.parent / "mash" / "intent.py")
    )
    assert violations == []


def test_no_module_level_def_detects_violation(tmp_path):
    path = write_py(tmp_path, "bad.py", """
        def my_function():
            pass
    """)
    checker = ConventionChecker()
    violations = checker.check_no_module_level_def(path)
    assert len(violations) == 1
    assert "my_function" in violations[0]


def test_no_module_level_def_allows_class(tmp_path):
    path = write_py(tmp_path, "ok.py", """
        class MyClass:
            def method(self):
                pass
    """)
    checker = ConventionChecker()
    violations = checker.check_no_module_level_def(path)
    assert violations == []


def test_check_no_sentinel_returns_clean(tmp_path):
    path = write_py(tmp_path, "flow.py", """
        from mash.exceptions.user_cancelled import UserCancelled

        class MyFlow:
            def run(self):
                try:
                    return "mv a b"
                except UserCancelled:
                    return None
    """)
    checker = ConventionChecker()
    violations = checker.check_no_sentinel_returns(path)
    assert violations == []


def test_check_no_sentinel_returns_detects_violation(tmp_path):
    path = write_py(tmp_path, "badflow.py", """
        class BadFlow:
            def run(self):
                return None
    """)
    checker = ConventionChecker()
    violations = checker.check_no_sentinel_returns(path)
    assert len(violations) == 1
    assert "BadFlow" in violations[0]


def test_check_no_sentinel_returns_ignores_non_flow(tmp_path):
    path = write_py(tmp_path, "helper.py", """
        class Helper:
            def get(self):
                return None
    """)
    checker = ConventionChecker()
    violations = checker.check_no_sentinel_returns(path)
    assert violations == []


def test_run_exits_0_on_clean_tree(tmp_path):
    path = write_py(tmp_path, "ok.py", """
        class MyClass:
            def method(self):
                pass
    """)
    checker = ConventionChecker()
    result = checker.run(str(tmp_path))
    assert result == 0


def test_run_exits_1_on_violation(tmp_path):
    write_py(tmp_path, "bad.py", """
        def top_level():
            pass
    """)
    checker = ConventionChecker()
    result = checker.run(str(tmp_path))
    assert result == 1


def test_run_skips_init_files(tmp_path):
    path = write_py(tmp_path, "__init__.py", """
        def helper():
            pass
    """)
    checker = ConventionChecker()
    result = checker.run(str(tmp_path))
    assert result == 0


def test_mash_tree_is_clean():
    checker = ConventionChecker()
    result = checker.run("mash/")
    assert result == 0
