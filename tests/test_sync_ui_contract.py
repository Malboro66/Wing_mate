import sys
from pathlib import Path

import pytest

pytest.importorskip("pytestqt")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ui.main_window import DataSyncThread
from app.ui.profile_tab import ProfileTab
from utils.notification_bus import NotificationLevel, notification_bus


def test_data_sync_thread_emits_loaded_payload_and_progress(qtbot):
    class _Processor:
        def process_campaign(self, _campaign_name):
            return {"pilot": {"name": "Pilot A"}, "missions": [{"id": 1}], "aces": []}

    progress_values = []
    thread = DataSyncThread(
        pwcgfc_path="/tmp/pwcg",
        campaign_name="camp1",
        processor_factory=lambda _path: _Processor(),
    )
    thread.progress.connect(progress_values.append)

    with qtbot.waitSignal(thread.data_loaded, timeout=3000) as loaded:
        thread.start()

    qtbot.waitUntil(lambda: not thread.isRunning(), timeout=3000)

    payload = loaded.args[0]
    assert payload["pilot"]["name"] == "Pilot A"
    assert payload["missions"]
    assert 100 in progress_values


def test_data_sync_thread_emits_error_for_empty_payload(qtbot):
    class _Processor:
        def process_campaign(self, _campaign_name):
            return {}

    progress_values = []
    thread = DataSyncThread(
        pwcgfc_path="/tmp/pwcg",
        campaign_name="camp1",
        processor_factory=lambda _path: _Processor(),
    )
    thread.progress.connect(progress_values.append)

    with qtbot.waitSignal(thread.error_occurred, timeout=3000) as error_signal:
        thread.start()

    qtbot.waitUntil(lambda: not thread.isRunning(), timeout=3000)

    assert "Não foi possível carregar" in error_signal.args[0]
    assert 0 in progress_values


def test_notification_bus_emits_qt_signal(qtbot):
    with qtbot.waitSignal(notification_bus.notified, timeout=1000) as notified:
        notification_bus.notify(NotificationLevel.WARNING, "Atenção", timeout_ms=2222)

    level, message, timeout_ms = notified.args
    assert level == NotificationLevel.WARNING.value
    assert message == "Atenção"
    assert timeout_ms == 2222


def test_profile_tab_updates_xp_and_morale_widgets(qtbot):
    tab = ProfileTab()
    qtbot.addWidget(tab)

    tab.set_xp(1750)
    tab.set_morale("🔥 Inspirado", 90)

    assert tab.xp_text_label.text() == "1750 XP"
    assert tab.morale_label.text() == "🔥 Inspirado (90)"
