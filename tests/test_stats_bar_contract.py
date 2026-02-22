from pathlib import Path


def test_stats_bar_widget_exists() -> None:
    src = Path("app/ui/widgets/stats_bar.py").read_text(encoding="utf-8")
    assert "class StatsBar(QWidget):" in src
    assert "def update_stat(self, label: str, value: str) -> None:" in src


def test_missions_tab_emits_stats_signal() -> None:
    src = Path("app/ui/missions_tab.py").read_text(encoding="utf-8")
    assert "stats_updated = pyqtSignal(int, int, str, str)" in src
    assert "self.stats_updated.connect(self._on_stats_updated, Qt.QueuedConnection)" in src
    assert "self.stats_updated.emit(len(self._missions), len(self._missions), first_date, last_date)" in src


def test_squadron_and_aces_emit_stats_signal() -> None:
    squad = Path("app/ui/squadron_tab.py").read_text(encoding="utf-8")
    assert "stats_updated = pyqtSignal(int, int, int, int)" in squad
    assert "self.stats_updated.connect(self._on_stats_updated, Qt.QueuedConnection)" in squad
    assert "self.stats_updated.emit(len(sorted_members), len(sorted_members), total_victories, total_missions)" in squad

    aces = Path("app/ui/aces_tab.py").read_text(encoding="utf-8")
    assert "stats_updated = pyqtSignal(int, int, str, int)" in aces
    assert "self.stats_updated.connect(self._on_stats_updated, Qt.QueuedConnection)" in aces
    assert "self.stats_updated.emit(len(aces), len(filtered_aces), top_name, top_victories)" in aces
