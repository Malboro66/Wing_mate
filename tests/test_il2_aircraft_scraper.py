import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.infrastructure.external.il2_aircraft_scraper import fetch_aircraft_specs


class _Resp:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


def test_fetch_aircraft_specs_parses_markdown_table(monkeypatch):
    fetch_aircraft_specs.cache_clear()

    markdown = """
| Spec | Value |
|---|---|
| Max speed | 560 km/h |
| Climb rate | 14.2 m/s |
| Turn time | 18.5 s |
| Engine power | 1700 hp |
| Wingspan | 9.8 m |
| Empty weight | 2540 kg |
| Gun type | MG 151/20 |
| Caliber | 20 mm |
"""

    def _fake_get(url, timeout):
        return _Resp(200, markdown)

    monkeypatch.setattr("app.infrastructure.external.il2_aircraft_scraper.httpx.get", _fake_get)

    data = fetch_aircraft_specs("bf-109-g6")

    assert data == {
        "max_speed_km_h": 560.0,
        "climb_rate_m_s": 14.2,
        "turn_time_s": 18.5,
        "engine_hp": 1700,
        "wingspan_m": 9.8,
        "empty_weight_kg": 2540,
        "gun_type": "MG 151/20",
        "caliber_mm": 20.0,
    }


def test_fetch_aircraft_specs_uses_lru_cache(monkeypatch):
    fetch_aircraft_specs.cache_clear()
    calls = {"n": 0}

    def _fake_get(url, timeout):
        calls["n"] += 1
        return _Resp(200, "| Spec | Value |\n|---|---|\n| Max speed | 500 km/h |")

    monkeypatch.setattr("app.infrastructure.external.il2_aircraft_scraper.httpx.get", _fake_get)

    first = fetch_aircraft_specs("yak-1")
    second = fetch_aircraft_specs("yak-1")

    assert first["max_speed_km_h"] == 500.0
    assert second["max_speed_km_h"] == 500.0
    assert calls["n"] == 1


def test_fetch_aircraft_specs_raises_when_not_found(monkeypatch):
    fetch_aircraft_specs.cache_clear()

    def _fake_get(url, timeout):
        return _Resp(404, "")

    monkeypatch.setattr("app.infrastructure.external.il2_aircraft_scraper.httpx.get", _fake_get)

    with pytest.raises(ValueError):
        fetch_aircraft_specs("missing-plane")
