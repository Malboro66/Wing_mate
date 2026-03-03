from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from utils.settings_manager import settings as settings_manager


@dataclass(frozen=True)
class WarPropagandaDecision:
    should_show_popup: bool
    victories_last_7d: int


class WarPropagandaTracker:
    """Rastreia vitórias recentes para disparar popup de propaganda de guerra."""

    KEY_EVENTS = "war_propaganda/victory_events"
    KEY_LAST_POPUP = "war_propaganda/last_popup_at"
    WINDOW_DAYS = 7
    THRESHOLD = 5

    _VICTORY_TOKENS = (
        "vitoria",
        "vitória",
        "abate",
        "victory",
        "kill",
        "killed",
        "shot down",
    )

    @staticmethod
    def _coerce_raw_events(raw: object) -> List[str]:
        if raw is None:
            return []
        if isinstance(raw, str):
            return [raw] if raw else []
        if isinstance(raw, (list, tuple)):
            return [str(item) for item in raw if str(item)]
        if isinstance(raw, dict):
            return [str(value) for value in raw.values() if str(value)]
        return [str(raw)]

    def _load_events(self) -> List[datetime]:
        raw = settings_manager.get(self.KEY_EVENTS, [])
        raw_items = self._coerce_raw_events(raw)

        out: List[datetime] = []
        for item in raw_items:
            try:
                out.append(datetime.fromisoformat(item))
            except ValueError:
                continue
        return out

    def _save_events(self, events: List[datetime]) -> None:
        settings_manager.set(self.KEY_EVENTS, [dt.isoformat() for dt in events])

    @classmethod
    def _is_victory_notification(cls, level: str, message: str) -> bool:
        if (level or "").lower() == "error":
            return False
        text = str(message or "").lower()
        return any(tok in text for tok in cls._VICTORY_TOKENS)

    def register_event_from_notification(
        self,
        level: str,
        message: str,
        now: datetime | None = None,
    ) -> WarPropagandaDecision:
        current = now or datetime.now()
        if not self._is_victory_notification(level, message):
            events = self._prune_old_events(self._load_events(), current)
            self._save_events(events)
            return WarPropagandaDecision(False, len(events))

        events = self._prune_old_events(self._load_events(), current)
        events.append(current)
        self._save_events(events)

        victories = len(events)
        if victories < self.THRESHOLD:
            return WarPropagandaDecision(False, victories)

        last_popup_at_raw = str(settings_manager.get(self.KEY_LAST_POPUP, "") or "")
        try:
            last_popup_at = datetime.fromisoformat(last_popup_at_raw) if last_popup_at_raw else None
        except ValueError:
            last_popup_at = None

        if last_popup_at and (current - last_popup_at) < timedelta(days=1):
            return WarPropagandaDecision(False, victories)

        settings_manager.set(self.KEY_LAST_POPUP, current.isoformat())
        return WarPropagandaDecision(True, victories)

    def _prune_old_events(self, events: List[datetime], now: datetime) -> List[datetime]:
        window_start = now - timedelta(days=self.WINDOW_DAYS)
        return [e for e in events if e >= window_start]
