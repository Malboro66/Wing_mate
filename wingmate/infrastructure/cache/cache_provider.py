from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CacheProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        raise NotImplementedError
