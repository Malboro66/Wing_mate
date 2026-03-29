from __future__ import annotations

from typing import Any, Dict


class ServiceContainer:
    def __init__(self) -> None:
        self._services: Dict[Any, Any] = {}

    def register(self, key: Any, value: Any) -> None:
        self._services[key] = value

    def resolve(self, key: Any) -> Any:
        return self._services[key]
