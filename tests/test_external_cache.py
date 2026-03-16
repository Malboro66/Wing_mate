import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.infrastructure.external_cache import ExternalCache


def test_external_cache_set_get_and_stale_flow(tmp_path: Path):
    cache = ExternalCache(tmp_path / "external_cache.db", default_ttl_days=30)

    assert cache.get("pilot:1") is None
    assert cache.is_stale("pilot:1") is True

    payload = {"name": "Pilot A", "victories": 4}
    cache.set("pilot:1", payload, source="example-source")

    assert cache.get("pilot:1") == payload
    assert cache.is_stale("pilot:1") is False


def test_external_cache_zero_ttl_marks_as_stale(tmp_path: Path):
    cache = ExternalCache(tmp_path / "external_cache.db", default_ttl_days=30)
    cache.set("key", {"ok": True}, source="src")

    import sqlite3

    conn = sqlite3.connect(str(tmp_path / "external_cache.db"))
    conn.execute("UPDATE external_cache SET ttl_days = 0 WHERE key = ?", ("key",))
    conn.commit()
    conn.close()

    assert cache.is_stale("key") is True
