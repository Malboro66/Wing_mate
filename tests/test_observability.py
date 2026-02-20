import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.observability import Events, emit_event


class _FakeStructuredLogger:
    def __init__(self) -> None:
        self.calls = []

    def log(self, level: str, message: str, **context):
        self.calls.append((level, message, context))


def test_emit_event_includes_standard_event_key():
    logger = _FakeStructuredLogger()

    emit_event(logger, Events.SYNC_STARTED, campaign_name="camp")

    assert len(logger.calls) == 1
    level, message, context = logger.calls[0]
    assert level == "info"
    assert message == Events.SYNC_STARTED
    assert context["event"] == Events.SYNC_STARTED
    assert context["campaign_name"] == "camp"
