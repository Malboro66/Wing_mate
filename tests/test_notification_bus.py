import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.notification_bus import NotificationLevel, notification_bus


def test_notification_bus_emits_events_to_subscribers():
    events = []

    def on_notify(level: str, message: str, timeout_ms: int):
        events.append((level, message, timeout_ms))

    notification_bus.notified.connect(on_notify)
    notification_bus.notify(NotificationLevel.INFO, "ok", 1234)

    assert events
    assert events[-1] == ("info", "ok", 1234)
