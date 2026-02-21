import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_tabs_use_ctrl_f_mixin_instead_of_keypress_override():
    missions = Path("app/ui/missions_tab.py").read_text(encoding="utf-8")
    squadron = Path("app/ui/squadron_tab.py").read_text(encoding="utf-8")

    assert "CtrlFFocusMixin" in missions
    assert "bind_ctrl_f_to_filter" in missions
    assert "def keyPressEvent" not in missions

    assert "CtrlFFocusMixin" in squadron
    assert "bind_ctrl_f_to_filter" in squadron
    assert "def keyPressEvent" not in squadron


def test_shortcut_mixin_uses_qshortcut_widget_with_children_context():
    src = Path("app/ui/shortcut_mixin.py").read_text(encoding="utf-8")
    assert "QShortcut" in src
    assert "WidgetWithChildrenShortcut" in src
