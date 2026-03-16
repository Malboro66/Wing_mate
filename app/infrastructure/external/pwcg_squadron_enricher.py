from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Optional

try:
    import httpx
except ImportError:  # pragma: no cover
    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen

    class _CompatResponse:
        def __init__(self, status_code: int, payload: Optional[Dict[str, Any]] = None) -> None:
            self.status_code = status_code
            self._payload = payload or {}

        def json(self) -> Dict[str, Any]:
            return dict(self._payload)

    class _HttpxCompat:
        @staticmethod
        def get(url: str, timeout: float = 15.0) -> _CompatResponse:
            try:
                with urlopen(url, timeout=timeout) as resp:
                    import json

                    body = resp.read().decode("utf-8", errors="replace")
                    return _CompatResponse(getattr(resp, "status", 200), json.loads(body or "{}"))
            except (HTTPError, URLError, ValueError):
                return _CompatResponse(404, {})

    httpx = _HttpxCompat()


_RAW_BASE = "https://raw.githubusercontent.com/PWCGDeveloper/PWCG/master"


def _candidate_urls(squad_id: str) -> list[str]:
    clean = str(squad_id or "").strip()
    return [
        f"{_RAW_BASE}/Data/Squadrons/{clean}.json",
        f"{_RAW_BASE}/Data/squadrons/{clean}.json",
        f"{_RAW_BASE}/data/squadrons/{clean}.json",
        f"{_RAW_BASE}/squadrons/{clean}.json",
    ]


def _pick(*values: Any) -> Optional[Any]:
    for value in values:
        if value is not None and str(value).strip() != "":
            return value
    return None


@lru_cache(maxsize=512)
def fetch_squadron_meta(squad_id: str) -> Dict[str, Any]:
    """Busca metadados de esquadrão no repositório oficial PWCG."""
    normalized_id = str(squad_id or "").strip()
    if not normalized_id:
        raise ValueError("squad_id cannot be empty")

    payload: Optional[Dict[str, Any]] = None
    for url in _candidate_urls(normalized_id):
        response = httpx.get(url, timeout=15.0)
        if response.status_code != 200:
            continue
        try:
            data = response.json()
        except ValueError:
            continue
        if isinstance(data, dict):
            payload = data
            break

    if payload is None:
        raise ValueError(f"squadron metadata not found for id: {normalized_id}")

    history = payload.get("history") if isinstance(payload.get("history"), dict) else {}

    return {
        "squadron_id": normalized_id,
        "name": _pick(payload.get("name"), payload.get("squadronName")),
        "country": _pick(payload.get("country"), payload.get("nation")),
        "front": _pick(payload.get("front"), history.get("front")),
        "theater": _pick(payload.get("theater"), payload.get("theatre"), history.get("theater")),
        "active_from": _pick(payload.get("activeFrom"), payload.get("startDate"), history.get("startDate")),
        "active_to": _pick(payload.get("activeTo"), payload.get("endDate"), history.get("endDate")),
        "raw": payload,
    }
