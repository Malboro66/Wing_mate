from __future__ import annotations

import re
from typing import Dict

ALIASES: Dict[str, str] = {
    "strutter": "Sopwith 1.5 Strutter",
    "sopwith strutter": "Sopwith 1.5 Strutter",
    "sopwith 1 5 strutter": "Sopwith 1.5 Strutter",
    "sopwith 1.5 strutter": "Sopwith 1.5 Strutter",
    "sopwith 1/2 strutter": "Sopwith 1.5 Strutter",
    "sopwith 1½ strutter": "Sopwith 1.5 Strutter",
}


def _normalize_key(model: str) -> str:
    text = str(model or "").strip().lower()
    text = text.replace("_", " ").replace("-", " ")
    text = text.replace("1½", "1.5")
    text = text.replace("½", "0.5")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def canonical(model: str) -> str:
    normalized = _normalize_key(model)
    if not normalized:
        return "N/A"

    fallback_key = re.sub(r"[^a-z0-9/ ]+", "", normalized)
    return ALIASES.get(normalized) or ALIASES.get(fallback_key) or str(model).strip() or "N/A"
