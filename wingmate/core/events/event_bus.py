from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, DefaultDict, Dict, List, Optional


@dataclass(frozen=True)
class Event:
    name: str
    payload: Dict[str, Any]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        self._subscribers[event_name].append(handler)

    def publish(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        event = Event(name=event_name, payload=payload or {})
        for handler in self._subscribers[event_name]:
            handler(event)
