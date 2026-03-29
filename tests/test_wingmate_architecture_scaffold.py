from pathlib import Path


def test_architecture_scaffold_directories_exist() -> None:
    expected = [
        "wingmate/core",
        "wingmate/presentation",
        "wingmate/application",
        "wingmate/domain",
        "wingmate/analytics",
        "wingmate/pipeline",
        "wingmate/infrastructure",
        "wingmate/observability",
        "wingmate/bootstrap",
    ]
    for rel in expected:
        assert Path(rel).is_dir(), rel


def test_main_uses_bootstrap_factory() -> None:
    src = Path("main.py").read_text(encoding="utf-8")
    assert "AppFactory" in src
    assert "AppFactory().start()" in src
