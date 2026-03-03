from __future__ import annotations

from datetime import date


def compute_flight_streak(last_sync_date: str, current_streak: int, today: date) -> tuple[int, str]:
    """Calcula a cadência de voo diária."""
    safe_streak = max(0, int(current_streak or 0))
    today_iso = today.isoformat()

    if not last_sync_date:
        return 1, today_iso

    try:
        last = date.fromisoformat(str(last_sync_date))
    except ValueError:
        return 1, today_iso

    delta_days = (today - last).days
    if delta_days == 0:
        return max(1, safe_streak), today_iso
    if delta_days == 1:
        return max(1, safe_streak + 1), today_iso
    return 1, today_iso
