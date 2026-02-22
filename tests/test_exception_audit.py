import ast
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _iter_json_exception_attrs(exc_node: ast.AST):
    if isinstance(exc_node, ast.Tuple):
        for item in exc_node.elts:
            yield from _iter_json_exception_attrs(item)
        return

    if isinstance(exc_node, ast.Attribute) and isinstance(exc_node.value, ast.Name):
        if exc_node.value.id == "json":
            yield exc_node.attr


def test_no_nonexistent_json_exceptions_are_caught():
    root = Path(__file__).resolve().parents[1]
    offenders = []

    for file_path in root.rglob("*.py"):
        if ".git" in file_path.parts:
            continue

        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler) or node.type is None:
                continue

            for attr in _iter_json_exception_attrs(node.type):
                if not hasattr(json, attr):
                    offenders.append(f"{file_path.relative_to(root)}:{node.lineno}: json.{attr}")

    assert not offenders, "Exceções json inexistentes capturadas: " + ", ".join(offenders)
