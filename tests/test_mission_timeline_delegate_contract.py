import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_missions_tab_registers_external_timeline_delegate_and_column():
    src = Path("app/ui/missions_tab.py").read_text(encoding="utf-8")
    assert "from app.ui.delegates.timeline_delegate import TimelineDelegate" in src
    assert "setColumnCount(5)" in src
    assert "setItemDelegateForColumn(4, self._timeline_delegate)" in src


def test_timeline_delegate_uses_qstyleditemdelegate_and_user_role_ratio():
    src = Path("app/ui/delegates/timeline_delegate.py").read_text(encoding="utf-8")
    assert "class TimelineDelegate(QStyledItemDelegate)" in src
    assert "Qt.UserRole" in src
