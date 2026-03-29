"""Gerenciador de cache persistente e instrumentado para a sessão atual.

Diagnóstico aplicado (observado antes das mudanças):
- os contadores de cache na observabilidade estavam em 0.0 porque eram derivados de
  cache em memória de parser por instância e em momento incorreto do fluxo.
- ao reiniciar o processo, esse cache em memória era perdido; não havia camada
  persistente entre sessões para produzir HITs reais na segunda execução.

Este módulo introduz cache persistente (diskcache/SQLite) + contadores por sessão,
com tolerância a falhas para não interromper a aplicação em caso de I/O.
"""

from __future__ import annotations

import atexit
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("IL2CampaignAnalyzer")

try:
    import diskcache  # type: ignore
except Exception:  # pragma: no cover - fallback quando dependência não está instalada
    diskcache = None

CACHE_DIR = Path.home() / ".wing_mate" / "cache"
_SESSION_HITS: int = 0
_SESSION_MISSES: int = 0


class _FallbackCache:
    """Fallback em memória para ambientes sem diskcache.

    Mantém API mínima compatível para o app seguir funcionando silenciosamente.
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def __len__(self) -> int:
        return len(self._data)

    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)

    def set(self, key: str, value: Any, expire: int = 0) -> None:
        del expire
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def close(self) -> None:
        return None


def _build_cache_backend() -> Any:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if diskcache is None:
            logger.warning("[cache] diskcache indisponível; usando fallback em memória")
            return _FallbackCache()
        return diskcache.Cache(str(CACHE_DIR))
    except Exception as exc:
        logger.warning("[cache] falha ao inicializar backend persistente: %s", exc)
        return _FallbackCache()


_disk = _build_cache_backend()


def inicializar_sessao() -> None:
    """Zera contadores da sessão atual sem apagar dados persistidos."""
    global _SESSION_HITS, _SESSION_MISSES
    _SESSION_HITS = 0
    _SESSION_MISSES = 0
    try:
        logger.info("[cache] sessão inicializada em %s — %s entradas", CACHE_DIR, len(_disk))
    except Exception:
        logger.info("[cache] sessão inicializada")


def get(key: str, ttl_check: bool = True) -> Optional[Any]:
    """Lê item do cache e contabiliza HIT/MISS da sessão."""
    del ttl_check
    global _SESSION_HITS, _SESSION_MISSES
    normalized_key = str(key or "").strip()
    if not normalized_key:
        _SESSION_MISSES += 1
        return None

    try:
        value = _disk.get(normalized_key)
        if value is not None:
            _SESSION_HITS += 1
            logger.debug("[cache] HIT key=%r", normalized_key)
            return value
    except Exception as exc:
        logger.debug("[cache] erro em get(%r): %s", normalized_key, exc)

    _SESSION_MISSES += 1
    logger.debug("[cache] MISS key=%r", normalized_key)
    return None


def set(key: str, value: Any, expire: int = 3600) -> None:
    """Grava item no cache persistente com TTL em segundos."""
    normalized_key = str(key or "").strip()
    if not normalized_key:
        return

    try:
        _disk.set(normalized_key, value, expire=max(1, int(expire)))
        logger.debug("[cache] SET key=%r expire=%ss", normalized_key, expire)
    except Exception as exc:
        logger.debug("[cache] erro em set(%r): %s", normalized_key, exc)


def invalidate(key: str) -> None:
    normalized_key = str(key or "").strip()
    if not normalized_key:
        return

    try:
        _disk.delete(normalized_key)
        logger.debug("[cache] DEL key=%r", normalized_key)
    except Exception as exc:
        logger.debug("[cache] erro em invalidate(%r): %s", normalized_key, exc)


def stats_para_observabilidade() -> dict[str, float]:
    total = _SESSION_HITS + _SESSION_MISSES
    hit_rate = (_SESSION_HITS / total) if total > 0 else 0.0
    return {
        "cache_hits": float(_SESSION_HITS),
        "cache_misses": float(_SESSION_MISSES),
        "cache_hit_rate": round(hit_rate, 4),
    }


def fechar() -> None:
    try:
        _disk.close()
    except Exception:
        return None


@atexit.register
def _close_cache_atexit() -> None:
    fechar()
