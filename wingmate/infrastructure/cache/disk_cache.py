from typing import Any

from wingmate.infrastructure.cache.cache_provider import CacheProvider


class DiskCache(CacheProvider):
    def get(self, key: str) -> Any:
        del key
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        del key, value, ttl_seconds
