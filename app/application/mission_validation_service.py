from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List

from utils.notification_bus import notify_warning

logger = logging.getLogger("IL2CampaignAnalyzer")


@dataclass(frozen=True)
class Mission:
    """Missão tipada para consumo da camada de apresentação."""

    date: str = ""
    time: str = ""
    aircraft: str = ""
    duty: str = ""
    description: str = ""


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
                    duty=str(raw.get("duty", "") or ""),
                    description=str(raw.get("description", "") or ""),
                )
            except (TypeError, ValueError) as e:
                logger.warning("Missão inválida no índice %s: %s", idx, e)
                invalid_count += 1
                continue

            out.append(mission)

        if invalid_count:
            notify_warning(f"{invalid_count} missão(ões) inválida(s) foram ignoradas.")

        return out
