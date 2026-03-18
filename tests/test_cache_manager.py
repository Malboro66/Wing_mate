import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cache_manager


def test_cache_manager_tracks_hits_and_misses() -> None:
    cache_manager.inicializar_sessao()
    cache_manager.invalidate("test:key:v1")

    assert cache_manager.get("test:key:v1") is None
    cache_manager.set("test:key:v1", {"ok": True}, expire=60)
    assert cache_manager.get("test:key:v1") == {"ok": True}

    stats = cache_manager.stats_para_observabilidade()
    assert stats["cache_misses"] >= 1
    assert stats["cache_hits"] >= 1
    assert stats["cache_hit_rate"] > 0


def test_cache_manager_stats_reset_per_session_but_data_persists() -> None:
    cache_manager.inicializar_sessao()
    cache_manager.set("test:persist:v1", [1, 2, 3], expire=60)
    assert cache_manager.get("test:persist:v1") == [1, 2, 3]

    cache_manager.inicializar_sessao()
    assert cache_manager.get("test:persist:v1") == [1, 2, 3]

    stats = cache_manager.stats_para_observabilidade()
    assert stats["cache_hits"] == 1.0
    assert stats["cache_misses"] == 0.0
    assert stats["cache_hit_rate"] == 1.0
