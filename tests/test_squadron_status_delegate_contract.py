import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_squadron_tab_uses_status_delegate_for_row_styling_and_icons():
    src = Path("app/ui/squadron_tab.py").read_text(encoding="utf-8")
    assert "class SquadronStatusDelegate(QStyledItemDelegate)" in src
    assert "self.table.setItemDelegate(self._status_delegate)" in src
    assert "STATUS_ICON" in src


def test_status_svg_icons_exist():
    icons = [
        "status_active.svg",
        "status_wounded.svg",
        "status_mia.svg",
        "status_kia.svg",
        "status_pow.svg",
        "status_hospital.svg",
        "status_leave.svg",
    ]
    base = Path("app/assets/icons")
    missing = [name for name in icons if not (base / name).exists()]
    assert not missing, f"Ícones SVG ausentes: {missing}"
