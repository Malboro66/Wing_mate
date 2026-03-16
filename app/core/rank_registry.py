from __future__ import annotations

from typing import Dict


RANKS: Dict[str, Dict[int, str]] = {
    "BRITAIN": {
        0: "Cadet",
        1: "Second Lieutenant",
        2: "Lieutenant",
        3: "Captain",
        4: "Major",
        5: "Lieutenant Colonel",
        6: "Colonel",
        7: "Brigadier",
    },
    "GERMANY": {
        0: "Fahnenjunker",
        1: "Leutnant",
        2: "Oberleutnant",
        3: "Hauptmann",
        4: "Major",
        5: "Oberstleutnant",
        6: "Oberst",
        7: "Generalmajor",
    },
    "FRANCE": {
        0: "Élève Officier",
        1: "Sous-lieutenant",
        2: "Lieutenant",
        3: "Capitaine",
        4: "Commandant",
        5: "Lieutenant-colonel",
        6: "Colonel",
        7: "Général de brigade",
    },
    "USA": {
        0: "Cadet",
        1: "Second Lieutenant",
        2: "First Lieutenant",
        3: "Captain",
        4: "Major",
        5: "Lieutenant Colonel",
        6: "Colonel",
        7: "Brigadier General",
    },
    "RUSSIA": {
        0: "Práporshchik",
        1: "Podporuchik",
        2: "Poruchik",
        3: "Shtabs-kapitan",
        4: "Kapitan",
        5: "Podpolkovnik",
        6: "Polkovnik",
        7: "General-mayor",
    },
}


def resolve_rank(country: str, rank_id: int) -> str:
    normalized_country = str(country or "").strip().upper()
    try:
        rank_idx = int(rank_id)
    except (TypeError, ValueError):
        return "N/A"

    ranks_by_country = RANKS.get(normalized_country)
    if not ranks_by_country:
        return "N/A"

    return ranks_by_country.get(rank_idx, "N/A")
