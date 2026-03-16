from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Dict, Optional

try:
    import httpx
except ImportError:  # pragma: no cover
    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen

    class _CompatResponse:
        def __init__(self, status_code: int, text: str = "") -> None:
            self.status_code = status_code
            self.text = text

    class _HttpxCompat:
        @staticmethod
        def get(url: str, timeout: float = 15.0) -> _CompatResponse:
            try:
                with urlopen(url, timeout=timeout) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
                    return _CompatResponse(getattr(resp, "status", 200), body)
            except HTTPError as exc:
                return _CompatResponse(getattr(exc, "code", 500), "")
            except URLError:
                return _CompatResponse(503, "")

    httpx = _HttpxCompat()


_REPO_RAW_BASE = "https://raw.githubusercontent.com/aergistal/il2/main"
_TABLE_ROW_RE = re.compile(r"^\|\s*(?P<key>[^|]+?)\s*\|\s*(?P<value>[^|]+?)\s*\|\s*$", re.MULTILINE)

_KEY_MAP = {
    "max speed": "max_speed_km_h",
    "maximum speed": "max_speed_km_h",
    "climb rate": "climb_rate_m_s",
    "turn time": "turn_time_s",
    "engine": "engine_hp",
    "power": "engine_hp",
    "wingspan": "wingspan_m",
    "empty weight": "empty_weight_kg",
    "gun": "gun_type",
    "caliber": "caliber_mm",
    "calibre": "caliber_mm",
}

_NUM_RE = re.compile(r"-?\d+(?:[.,]\d+)?")


def _normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", str(label or "").strip().lower())


def _extract_number(value: str) -> Optional[float]:
    match = _NUM_RE.search(str(value or ""))
    if not match:
        return None
    number_text = match.group(0).replace(",", ".")
    try:
        return float(number_text)
    except ValueError:
        return None


def _coerce_value(field: str, raw_value: str) -> Any:
    if field == "gun_type":
        return str(raw_value or "").strip()

    parsed = _extract_number(raw_value)
    if parsed is None:
        return None

    if field in {"engine_hp", "empty_weight_kg"}:
        return int(round(parsed))
    return float(parsed)


def _build_markdown_urls(slug: str) -> list[str]:
    clean_slug = str(slug or "").strip().strip("/")
    return [
        f"{_REPO_RAW_BASE}/{clean_slug}.md",
        f"{_REPO_RAW_BASE}/aircraft/{clean_slug}.md",
        f"{_REPO_RAW_BASE}/planes/{clean_slug}.md",
    ]


@lru_cache(maxsize=256)
def fetch_aircraft_specs(slug: str) -> Dict[str, Any]:
    """Busca specs técnicas da aeronave no repo público e parseia tabela Markdown."""
    normalized_slug = str(slug or "").strip().strip("/")
    if not normalized_slug:
        raise ValueError("slug cannot be empty")

    markdown: Optional[str] = None
    for url in _build_markdown_urls(normalized_slug):
        response = httpx.get(url, timeout=15.0)
        if response.status_code == 200:
            markdown = response.text
            break

    if markdown is None:
        raise ValueError(f"aircraft spec markdown not found for slug: {normalized_slug}")

    specs: Dict[str, Any] = {
        "max_speed_km_h": None,
        "climb_rate_m_s": None,
        "turn_time_s": None,
        "engine_hp": None,
        "wingspan_m": None,
        "empty_weight_kg": None,
        "gun_type": None,
        "caliber_mm": None,
    }

    for match in _TABLE_ROW_RE.finditer(markdown):
        key_label = _normalize_label(match.group("key"))
        value_text = str(match.group("value") or "").strip()

        if set(key_label) <= {"-", ":", " "}:
            continue

        mapped_field = None
        for key_hint, field in _KEY_MAP.items():
            if key_hint in key_label:
                mapped_field = field
                break

        if not mapped_field:
            continue

        coerced = _coerce_value(mapped_field, value_text)
        if coerced is not None and specs.get(mapped_field) is None:
            specs[mapped_field] = coerced

    return specs
