import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.infrastructure.external.pwcg_squadron_enricher import fetch_squadron_meta


class _Resp:
    def __init__(self, status_code: int, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_fetch_squadron_meta_parses_fields(monkeypatch):
    fetch_squadron_meta.cache_clear()

    payload = {
        "name": "Jasta 11",
        "country": "GERMANY",
        "front": "Western",
        "theater": "France",
        "activeFrom": "1916-01-01",
        "activeTo": "1918-11-11",
    }

    def _fake_get(url, timeout):
        return _Resp(200, payload)

    monkeypatch.setattr("app.infrastructure.external.pwcg_squadron_enricher.httpx.get", _fake_get)

    meta = fetch_squadron_meta("11")

    assert meta["squadron_id"] == "11"
    assert meta["name"] == "Jasta 11"
    assert meta["country"] == "GERMANY"
    assert meta["front"] == "Western"
    assert meta["theater"] == "France"
    assert meta["active_from"] == "1916-01-01"
    assert meta["active_to"] == "1918-11-11"


def test_fetch_squadron_meta_uses_cache(monkeypatch):
    fetch_squadron_meta.cache_clear()
    calls = {"n": 0}

    def _fake_get(url, timeout):
        calls["n"] += 1
        return _Resp(200, {"name": "Escadrille 3"})

    monkeypatch.setattr("app.infrastructure.external.pwcg_squadron_enricher.httpx.get", _fake_get)

    a = fetch_squadron_meta("3")
    b = fetch_squadron_meta("3")

    assert a["name"] == "Escadrille 3"
    assert b["name"] == "Escadrille 3"
    assert calls["n"] == 1


def test_fetch_squadron_meta_not_found(monkeypatch):
    fetch_squadron_meta.cache_clear()

    def _fake_get(url, timeout):
        return _Resp(404, {})

    monkeypatch.setattr("app.infrastructure.external.pwcg_squadron_enricher.httpx.get", _fake_get)

    with pytest.raises(ValueError):
        fetch_squadron_meta("99999")
