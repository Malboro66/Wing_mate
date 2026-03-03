import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.flight_streak import compute_flight_streak


def test_flight_streak_starts_at_one_when_no_history():
    streak, day = compute_flight_streak("", 0, date(2026, 3, 1))
    assert streak == 1
    assert day == "2026-03-01"


def test_flight_streak_increments_when_last_sync_was_yesterday():
    today = date(2026, 3, 10)
    streak, _ = compute_flight_streak((today - timedelta(days=1)).isoformat(), 4, today)
    assert streak == 5


def test_flight_streak_resets_when_gap_is_greater_than_one_day():
    today = date(2026, 3, 10)
    streak, _ = compute_flight_streak((today - timedelta(days=3)).isoformat(), 7, today)
    assert streak == 1
