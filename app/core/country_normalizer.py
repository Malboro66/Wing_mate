from __future__ import annotations

from typing import Any, Final

CANONICAL_COUNTRY_DISPLAY_NAMES: Final[dict[str, str]] = {
    "GERMANY": "Germany",
    "BRITAIN": "Great Britain",
    "FRANCE": "France",
    "USA": "USA",
    "BELGIAN": "Belgium",
}

COUNTRY_ROUNDEL_STEMS: Final[dict[str, str]] = {
    "GERMANY": "theme_german",
    "BRITAIN": "theme_rfc",
    "FRANCE": "theme_french",
    "USA": "theme_american",
    "BELGIAN": "theme_belgium",
}

_COUNTRY_ALIASES: Final[dict[str, str]] = {
    "GER": "GERMANY",
    "DE": "GERMANY",
    "DEU": "GERMANY",
    "ALEMANHA": "GERMANY",
    "ALLEMAGNE": "GERMANY",
    "DEUTSCHLAND": "GERMANY",
    "GERMAN": "GERMANY",
    "GERMANS": "GERMANY",
    "DEUTSCH": "GERMANY",
    "PRUSSIA": "GERMANY",
    "PRUSSIAN": "GERMANY",
    "PRUSSIANS": "GERMANY",
    "FRA": "FRANCE",
    "FR": "FRANCE",
    "FRENCH": "FRANCE",
    "GB": "BRITAIN",
    "GBR": "BRITAIN",
    "UK": "BRITAIN",
    "BRIT": "BRITAIN",
    "UNITED KINGDOM": "BRITAIN",
    "GREAT BRITAIN": "BRITAIN",
    "BRITISH": "BRITAIN",
    "ENGLAND": "BRITAIN",
    "RFC": "BRITAIN",
    "RNAS": "BRITAIN",
    "BEL": "BELGIAN",
    "BE": "BELGIAN",
    "BELGIUM": "BELGIAN",
    "BELGIAN": "BELGIAN",
    "BELGE": "BELGIAN",
    "US": "USA",
    "UNITED STATES": "USA",
    "UNITED STATES OF AMERICA": "USA",
    "AMERICAN": "USA",
}

_SUBSTRING_ALIASES: Final[tuple[tuple[str, str], ...]] = (
    ("GREAT BRITAIN", "BRITAIN"),
    ("UNITED KINGDOM", "BRITAIN"),
    ("RFC", "BRITAIN"),
    ("RNAS", "BRITAIN"),
    ("BRITISH", "BRITAIN"),
    ("ENGLAND", "BRITAIN"),
    ("GERMAN", "GERMANY"),
    ("DEUTSCH", "GERMANY"),
    ("PRUSSIA", "GERMANY"),
    ("PRUSSIAN", "GERMANY"),
    ("FRENCH", "FRANCE"),
    ("UNITED STATES", "USA"),
    ("AMERICAN", "USA"),
    ("BELGIAN", "BELGIAN"),
    ("BELGIUM", "BELGIAN"),
    ("BELGE", "BELGIAN"),
)


def canonicalize_country_code(raw_country: Any, default: str = "GERMANY") -> str:
    value = str(raw_country or "").strip().upper()
    if not value:
        return default
    if value in _COUNTRY_ALIASES:
        return _COUNTRY_ALIASES[value]
    for alias, canonical in _SUBSTRING_ALIASES:
        if alias in value:
            return canonical
    return value


def country_display_name(raw_country: Any, default: str = "Germany") -> str:
    canonical = canonicalize_country_code(raw_country)
    return CANONICAL_COUNTRY_DISPLAY_NAMES.get(canonical, default)
