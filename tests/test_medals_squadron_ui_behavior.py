import sys
from pathlib import Path

import pytest

pytest.importorskip("pytestqt")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ui.medals_tab import MedalsTab
from app.ui.squadron_tab import SquadronTab


def test_medals_tab_switches_between_grid_and_list_modes(qtbot):
    tab = MedalsTab()
    qtbot.addWidget(tab)

    assert tab._icon_list is not None
    assert tab._table is not None
    assert tab._mode_combo is not None

    tab._mode_combo.setCurrentIndex(0)
    qtbot.waitUntil(lambda: tab._icon_list.isVisible())
    assert not tab._table.isVisible()

    tab._mode_combo.setCurrentIndex(1)
    qtbot.waitUntil(lambda: tab._table.isVisible())
    assert not tab._icon_list.isVisible()


def test_squadron_tab_stats_signal_emits_expected_totals(qtbot):
    tab = SquadronTab()
    qtbot.addWidget(tab)

    members = [
        {
            "name": "Pilot A",
            "rank": "Leutnant",
            "victories": 2,
            "missions_flown": 5,
            "status": "Ativo",
        },
        {
            "name": "Pilot B",
            "rank": "Major",
            "victories": 3,
            "missions_flown": 7,
            "status": "KIA",
        },
    ]

    with qtbot.waitSignal(tab.stats_updated, timeout=1000) as signal:
        tab.set_squadron(members)

    total, visible, victories, missions = signal.args
    assert total == 2
    assert visible == 2
    assert victories == 5
    assert missions == 12


def test_squadron_tab_filter_updates_visible_stats(qtbot):
    tab = SquadronTab()
    qtbot.addWidget(tab)

    members = [
        {
            "name": "Pilot Active",
            "rank": "Leutnant",
            "victories": 4,
            "missions_flown": 8,
            "status": "Ativo",
        },
        {
            "name": "Pilot Down",
            "rank": "Major",
            "victories": 1,
            "missions_flown": 2,
            "status": "KIA",
        },
    ]

    tab.set_squadron(members)

    with qtbot.waitSignal(tab.stats_updated, timeout=1000) as signal:
        tab.filter_edit.setText("Active")

    total, visible, victories, missions = signal.args
    assert total == 2
    assert visible == 1
    assert victories == 4
    assert missions == 8
