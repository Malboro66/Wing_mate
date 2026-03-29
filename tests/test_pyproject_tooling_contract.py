from pathlib import Path

import tomli


def test_pyproject_declares_ruff_in_dev_and_tool_config():
    data = tomli.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    dev_deps = data["project"]["optional-dependencies"]["dev"]
    assert any(dep.startswith("ruff>=") for dep in dev_deps)

    assert "ruff" in data["tool"]
    assert "lint" in data["tool"]["ruff"]
    assert "format" in data["tool"]["ruff"]
