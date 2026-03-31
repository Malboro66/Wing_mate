from pathlib import Path


def test_squadron_tab_accepts_cpdb_fallback_overview_when_meta_missing():
    src = Path("app/ui/squadron_tab.py").read_text(encoding="utf-8")
    assert "def set_squad_overview(self, squad_name: str, fallback_overview: Optional[Dict[str, Any]] = None) -> None:" in src
    assert "self._render_cpdb_overview_html(fallback_overview)" in src
    assert "Metadados do esquadrão não encontrados." in src
