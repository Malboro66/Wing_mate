from pathlib import Path


def test_medal_hover_popup_widget_exists() -> None:
    src = Path("app/ui/widgets/medal_hover_popup.py").read_text(encoding="utf-8")
    assert "class MedalHoverPopup(QWidget):" in src
    assert "DELAY_MS = 600" in src
    assert "self._timer.timeout.connect(self.show)" in src


def test_medals_tab_integrates_hover_popup() -> None:
    src = Path("app/ui/medals_tab.py").read_text(encoding="utf-8")
    assert "from app.ui.widgets.medal_hover_popup import MedalHoverPopup" in src
    assert "self._hover_popup = MedalHoverPopup(self)" in src
    assert "self._icon_list.mouseMoveEvent = self._on_icon_hover" in src
    assert "def _on_icon_hover(" in src
