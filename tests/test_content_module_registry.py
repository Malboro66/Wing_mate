import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.content_module_registry import ContentModuleRegistry


def test_registry_exposes_builtin_modules(tmp_path: Path):
    registry = ContentModuleRegistry(tmp_path)

    modules = registry.list_modules()
    ids = [m.module_id for m in modules]

    assert "medals" in ids
    assert "squadrons" in ids
    assert "ranks" in ids


def test_registry_loads_external_manifest(tmp_path: Path):
    assets_root = tmp_path / "assets"
    modules_root = assets_root / "modules" / "ww1-pack"
    modules_root.mkdir(parents=True, exist_ok=True)

    (modules_root / "module.json").write_text(
        '{"id":"ww1_pack","name":"WW1 Pack","category":"medals","path":"content","version":"1.1.0"}',
        encoding="utf-8",
    )
    (modules_root / "content").mkdir(parents=True, exist_ok=True)

    registry = ContentModuleRegistry(assets_root)
    loaded = registry.load_external_modules()

    assert loaded == 1
    module = registry.get_module("ww1_pack")
    assert module is not None
    assert module.version == "1.1.0"
    assert module.base_path == (modules_root / "content").resolve()


def test_registry_resolve_raises_for_missing_module(tmp_path: Path):
    registry = ContentModuleRegistry(tmp_path)

    try:
        registry.resolve("missing", "file.json")
        assert False, "Era esperado KeyError"
    except KeyError:
        assert True
