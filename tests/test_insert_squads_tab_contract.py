from pathlib import Path


def test_insert_squads_tab_uses_content_registry_resolve_for_squadron_assets():
    src = Path("app/ui/insert_squads_tab.py").read_text(encoding="utf-8")

    assert 'self._content_registry.resolve("squadrons", "images")' in src
    assert 'self._content_registry.resolve("squadrons", "meta")' in src
    assert 'self._assets_root' not in src
