from typing import Any, Dict

from wingmate.infrastructure.cache.cache_provider import CacheProvider


class MemoryCache(CacheProvider):
    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def get(self, key: str) -> Any:
        return self._data.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        del ttl_seconds
        self._data[key] = value
