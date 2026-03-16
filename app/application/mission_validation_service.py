from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional

from utils.notification_bus import notify_warning

logger = logging.getLogger("IL2CampaignAnalyzer")


class DataSource(str, Enum):
    PWCG_JSON = "pwcg_json"
    VANILLA_DB = "vanilla_db"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Mission:
    """Missão tipada para consumo da camada de apresentação."""

    date: str = ""
    time: str = ""
    aircraft: str = ""
    aircraft_badge: str = ""
    duty: str = ""
    locality: str = ""
    airfield: str = ""
    weather: str = ""
    description: str = ""
    flight_time_formatted: str = ""
    victories: Optional[int] = None
    status: Optional[int] = None
    score: Optional[int] = None
    flight_time_s: Optional[int] = None
    source: DataSource = DataSource.UNKNOWN


def _parse_source(raw_source: Any) -> DataSource:
    value = str(raw_source or "").strip().lower()
    if value == DataSource.PWCG_JSON.value:
        return DataSource.PWCG_JSON
    if value == DataSource.VANILLA_DB.value:
        return DataSource.VANILLA_DB
    return DataSource.UNKNOWN


class MissionValidationService:
    """Valida payloads de missão uma única vez na entrada da aplicação."""

    @staticmethod
    def validate(raw_missions: Any) -> List[Mission]:
        if not isinstance(raw_missions, list):
            return []

        out: List[Mission] = []
        invalid_count = 0
        for idx, raw in enumerate(raw_missions):
            if not isinstance(raw, dict):
                logger.warning("Missão inválida no índice %s: esperado dict, recebido %s", idx, type(raw).__name__)
                invalid_count += 1
                continue

            try:
                mission = Mission(
                    date=str(raw.get("date", "") or ""),
                    time=str(raw.get("time", "") or ""),
                    aircraft=str(raw.get("aircraft", "") or ""),
                    aircraft_badge=str(raw.get("aircraft_badge", "") or ""),
                    duty=str(raw.get("duty", "") or ""),
                    locality=str(raw.get("locality", "") or ""),
                    airfield=str(raw.get("airfield", "") or ""),
                    weather=str(raw.get("weather", "") or ""),
                    description=str(raw.get("description", "") or ""),
                    flight_time_formatted=str(raw.get("flight_time_formatted", "") or ""),
                    victories=int(raw["victories"]) if raw.get("victories") is not None else None,
                    status=int(raw["status"]) if raw.get("status") is not None else None,
                    score=int(raw["score"]) if raw.get("score") is not None else None,
                    flight_time_s=int(raw["flight_time_s"]) if raw.get("flight_time_s") is not None else None,
                    source=_parse_source(raw.get("source")),
                )
            except (TypeError, ValueError) as e:
                logger.warning("Missão inválida no índice %s: %s", idx, e)
                invalid_count += 1
                continue

            out.append(mission)

        if invalid_count:
            notify_warning(f"{invalid_count} missão(ões) inválida(s) foram ignoradas.")

        return out
