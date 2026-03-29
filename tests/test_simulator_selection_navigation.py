from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

pytest.importorskip("PyQt5")

from app.ui.design_system import build_global_stylesheet, set_theme
from app.ui.main_window import MainWindow as WingMateMainWindow
from app.ui.simulator_selection_main_window import MainWindow
from app.ui.ww1_simulator_selection_widget import WW1SimulatorSelectionWidget


def test_resolve_data_source_mode_for_known_simulators():
    assert (
        MainWindow._resolve_data_source_mode(WW1SimulatorSelectionWidget.SIM_IL2_VANILLA)
        == WingMateMainWindow.SOURCE_IL2_VANILLA
    )
    assert (
        MainWindow._resolve_data_source_mode(WW1SimulatorSelectionWidget.SIM_IL2_PWCG)
        == WingMateMainWindow.SOURCE_PWCG_JSON
    )
    assert (
        MainWindow._resolve_data_source_mode(WW1SimulatorSelectionWidget.SIM_ROF_PWCG)
        == WingMateMainWindow.SOURCE_PWCG_JSON
    )
    assert (
        MainWindow._resolve_data_source_mode(WW1SimulatorSelectionWidget.SIM_ROF_VANILLA)
        == WingMateMainWindow.SOURCE_PWCG_JSON
    )


def test_go_to_and_go_back_history_pop_behavior_via_source_inspection():
    src = Path("app/ui/simulator_selection_main_window.py").read_text(encoding="utf-8")
    assert "def _go_to(self, idx: int) -> None:" in src
    assert "self._history.append(cur)" in src
    assert "def _go_back(self) -> None:" in src
    assert "self.stack.setCurrentIndex(self._history.pop())" in src


def test_resolve_pwcg_campaign_path_user_campaigns_layout(tmp_path: Path):
    root = tmp_path / "PWCG"
    campaigns = root / "User" / "Campaigns"
    campaigns.mkdir(parents=True)

    resolved = MainWindow._resolve_pwcg_campaign_path(str(root))
    assert resolved == str(root)


def test_build_global_stylesheet_smoke_dark_vs_light():
    set_theme("dark")
    dark = build_global_stylesheet()

    set_theme("light")
    light = build_global_stylesheet()

    assert dark and light
    assert dark != light
    assert "QWidget" in dark and "QWidget" in light
    assert "QTabBar::tab" in dark and "QTabBar::tab" in light


def test_resolve_candidate_drive_roots_non_empty_and_deduplicated():
    roots = MainWindow._candidate_drive_roots()
    assert roots
    as_text = [str(p).upper() for p in roots]
    assert len(as_text) == len(set(as_text))
