import sys
from pathlib import Path

import pytest

pytest.importorskip("pytestqt")
pytest.importorskip("PyQt5.QtCore")
pytest.importorskip("PyQt5.QtWidgets")

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidgetItem

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ui.medals_tab import MedalsTab
from app.ui.squadron_tab import SquadronTab


def test_medals_tab_switches_between_grid_and_list_modes(qtbot):
    tab = MedalsTab()
    qtbot.addWidget(tab)

    assert tab._icon_list is not None
    assert tab._table is not None
    assert tab._mode_combo is not None

    tab.show()

    tab._mode_combo.setCurrentIndex(0)
    qtbot.waitUntil(lambda: not tab._icon_list.isHidden())
    assert tab._table.isHidden()

    tab._mode_combo.setCurrentIndex(1)
    qtbot.waitUntil(lambda: not tab._table.isHidden())
    assert tab._icon_list.isHidden()


def test_medals_tab_avoids_reopening_details_after_close(qtbot, monkeypatch):
    tab = MedalsTab()
    qtbot.addWidget(tab)
    tab.show()

    assert tab._icon_list is not None

    call_count = 0

    def _fake_open_details(_rec):
        nonlocal call_count
        call_count += 1

    monkeypatch.setattr(tab, "_open_details", _fake_open_details)

    item = QListWidgetItem("Medalha de teste")
    item.setData(Qt.UserRole, {"id": "test_medal", "name": "Teste"})
    tab._icon_list.addItem(item)

    # itemActivated abre detalhes; itemDoubleClicked não deve disparar
    # novamente para evitar reabertura após fechar.
    tab._icon_list.itemActivated.emit(item)
    tab._icon_list.itemDoubleClicked.emit(item)

    assert call_count == 1


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


def test_squadron_tab_filter_by_rank_uses_rank_label_text(qtbot):
    tab = SquadronTab()
    qtbot.addWidget(tab)

    members = [
        {
            "name": "Pilot Alpha",
            "rank": "Leutnant",
            "victories": 2,
            "missions_flown": 5,
            "status": "Ativo",
        },
        {
            "name": "Pilot Bravo",
            "rank": "Major",
            "victories": 3,
            "missions_flown": 7,
            "status": "Ativo",
        },
    ]

    tab.set_squadron(members)

    with qtbot.waitSignal(tab.stats_updated, timeout=1000) as signal:
        tab.filter_edit.setText("Major")

    total, visible, victories, missions = signal.args
    assert total == 2
    assert visible == 1
    assert victories == 3
    assert missions == 7
