import ast
import sys
from pathlib import Path


class ConventionChecker:
    def check_no_module_level_def(self, python_file_path: str) -> list[str]:
        source = Path(python_file_path).read_text()
        tree = ast.parse(source, filename=python_file_path)
        violations = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                violations.append(
                    f"{python_file_path}:{node.lineno}: module-level def '{node.name}'"
                )
        return violations

    def check_no_sentinel_returns(self, python_file_path: str) -> list[str]:
        source = Path(python_file_path).read_text()
        tree = ast.parse(source, filename=python_file_path)
        violations = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not (node.name.endswith("Flow") or node.name.endswith("Selector")):
                continue
            for item in ast.walk(node):
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for child in ast.walk(item):
                    if not isinstance(child, ast.Return):
                        continue
                    if self._is_sentinel_return(child) and not self._inside_except(child, item):
                        violations.append(
                            f"{python_file_path}:{child.lineno}: sentinel return in"
                            f" {node.name}.{item.name}"
                        )
        return violations

    def _is_sentinel_return(self, node: ast.Return) -> bool:
        if node.value is None:
            return False
        value = node.value
        if isinstance(value, ast.Constant) and value.value is None:
            return True
        if isinstance(value, ast.Tuple):
            return any(
                isinstance(element, ast.Constant) and element.value is None
                for element in value.elts
            )
        return False

    def _inside_except(self, return_node: ast.Return, function_node: ast.FunctionDef) -> bool:
        for node in ast.walk(function_node):
            if not isinstance(node, ast.ExceptHandler):
                continue
            for child in ast.walk(node):
                if child is return_node:
                    return True
        return False

    def run(self, directory: str) -> int:
        violations = []
        for path in sorted(Path(directory).rglob("*.py")):
            if path.name == "__init__.py":
                continue
            violations.extend(self.check_no_module_level_def(str(path)))
            violations.extend(self.check_no_sentinel_returns(str(path)))
        if violations:
            for message in violations:
                print(message, file=sys.stderr)
            return 1
        return 0


if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "mash/"
    sys.exit(ConventionChecker().run(directory))
