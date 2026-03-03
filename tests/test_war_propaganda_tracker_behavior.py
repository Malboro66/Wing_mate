import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime

import pytest

pytest.importorskip("PyQt5")

from utils.war_propaganda_tracker import WarPropagandaTracker


def test_tracker_coerces_qsettings_like_collections() -> None:
    tracker = WarPropagandaTracker()
    now = datetime(1918, 1, 1, 10, 0, 0)

    raw_dict = {"0": now.isoformat(), "1": "invalid"}
    result = tracker._coerce_raw_events(raw_dict)

    assert result[0] == now.isoformat()
    assert "invalid" in result


def test_tracker_load_events_accepts_dict_payload(monkeypatch) -> None:
    tracker = WarPropagandaTracker()
    now = datetime(1918, 1, 1, 10, 0, 0)

    class _Settings:
        @staticmethod
        def get(_key, _default=None):
            return {"a": now.isoformat(), "b": "invalid"}

    monkeypatch.setattr("utils.war_propaganda_tracker.settings_manager", _Settings)

    events = tracker._load_events()
    assert events == [now]
