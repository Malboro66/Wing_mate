# -*- coding: utf-8 -*-
"""
Wing Mate â€” app/infrastructure/cp_db_repository.py

ImplementaÃ§Ã£o concreta de CampaignRepositoryPort que lÃª dados do cp.db.

Uso:
    from app.infrastructure.cp_db_repository import CpDbCampaignRepository
    repo = CpDbCampaignRepository(Path("/path/to/cp.db"))
    campaign = repo.get_campaign("1")          # id como string
    missions  = repo.get_missions("1", "abc")  # ignora serial no modo db
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.repositories import Campaign, CampaignRepositoryPort
from app.infrastructure.cp_db_mapper import CpDbMapper
from app.infrastructure.cp_db_reader import CpDbReader
from app.infrastructure.vanilla_mission_report import VanillaMissionReportReader

logger = logging.getLogger("IL2CampaignAnalyzer")


class CpDbCampaignRepository:
    """Implementa CampaignRepositoryPort sobre o banco SQLite cp.db."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._reader = CpDbReader(db_path)
        self._mapper = CpDbMapper()
        self._mission_report_reader = VanillaMissionReportReader(db_path)

    # ------------------------------------------------------------------ #
    # CampaignRepositoryPort                                               #
    # ------------------------------------------------------------------ #

    def get_campaign(self, name: str) -> Optional[Campaign]:
        """
        name: pode ser o id numÃ©rico da carreira (como string)
              ou "active" para buscar a carreira ativa.
        """
        try:
            career_id: Optional[int] = None
            if name.isdigit():
                career_id = int(name)

            career = self._reader.get_active_career(career_id)
            if not career:
                logger.warning("cp.db: carreira '%s' nÃ£o encontrada", name)
                return None

            personage_id = str(career.get("personageId", ""))
            personage = self._reader.get_personage(personage_id) if personage_id else None
            pilot = self._reader.get_player_pilot(personage_id) if personage_id else None
            squadron = self._reader.get_squadron(int(career.get("squadronId", -1)))

            info = CpDbMapper.career_to_campaign_dict(career, personage, pilot, squadron)

            return Campaign(
                name=str(career["id"]),
                player_serial=info["player_serial"],
                squadron_name=info["squadron_name"],
                reference_date=info["reference_date"] or None,
            )
        except Exception:
            logger.exception("cp.db: falha ao obter campanha '%s'", name)
            return None

    def get_missions(self, campaign_name: str, serial: str) -> List[Dict[str, Any]]:
        """
        Retorna lista de dicts de missÃµes no formato esperado pelos ViewModels.
        serial: ignorado (no db, o vÃ­nculo Ã© via careerId / personageId).
        """
        try:
            career_id = int(campaign_name) if campaign_name.isdigit() else None
            if career_id is None:
                career = self._reader.get_active_career()
                if not career:
                    return []
                career_id = int(career["id"])

            personage_id = str(
                (self._reader.get_active_career(career_id) or {}).get("personageId", "")
            )
            pilot = self._reader.get_player_pilot(personage_id) if personage_id else None
            if not pilot:
                return []

            pilot_id = int(pilot["id"])
            sorties = self._reader.get_pilot_sorties(pilot_id)

            # Ãndice de missions por id para enriquecer cada sortie
            missions_list = self._reader.get_missions(career_id)
            missions_by_id: Dict[int, Dict[str, Any]] = {
                int(m["id"]): m for m in missions_list
            }

            missions_data = CpDbMapper.sorties_to_missions(sorties, missions_by_id)
            self._enrich_latest_mission_with_flight_log(missions_data)
            return missions_data
        except Exception:
            logger.exception("cp.db: falha ao obter missÃµes da carreira '%s'", campaign_name)
            return []

    # ------------------------------------------------------------------ #
    # MÃ©todos extras (nÃ£o exigidos pela porta, mas Ãºteis para MainWindow)  #
    # ------------------------------------------------------------------ #

    def list_career_ids(self) -> List[str]:
        """Lista IDs de carreiras disponÃ­veis (para popular o combo de campanhas)."""
        try:
            return [str(c["id"]) for c in self._reader.list_careers()]
        except Exception:
            logger.exception("cp.db: falha ao listar carreiras")
            return []

    def process_career(self, career_id_str: str) -> Dict[str, Any]:
        """
        Equivalente ao IL2DataProcessor.process_campaign() mas para o banco.
        Retorna o mesmo dict esperado por MainWindow._on_data_loaded().
        """
        try:
            career_id = int(career_id_str) if career_id_str.isdigit() else None
            career = self._reader.get_active_career(career_id)
            if not career:
                return {}

            career_id = int(career["id"])
            personage_id = str(career.get("personageId", ""))
            pilot_row = self._reader.get_player_pilot(personage_id)
            squadron_row = self._reader.get_squadron(int(career.get("squadronId", -1)))
            all_pilots = self._reader.get_pilots(int(career.get("squadronId", -1)))
            sorties = self._reader.get_pilot_sorties(int(pilot_row["id"])) if pilot_row else []
            missions_list = self._reader.get_missions(career_id)
            missions_by_id = {int(m["id"]): m for m in missions_list}
            awards = self._reader.get_pilot_awards(int(pilot_row["id"])) if pilot_row else []
            aces_list = self._reader.get_aces(career_id)

            squad_name = "N/A"
            if squadron_row:
                squad_name = str(squadron_row.get("name") or squadron_row.get("airfield", "N/A"))

            pilot_data = CpDbMapper.pilot_to_pilot_data(
                pilot_row or {}, sorties, squad_name
            )
            missions_data = CpDbMapper.sorties_to_missions(sorties, missions_by_id)
            self._enrich_latest_mission_with_flight_log(missions_data)
            squadron_data = CpDbMapper.pilots_to_squadron(all_pilots)
            aces_data = CpDbMapper.aces_to_aces_data(aces_list)
            aircraft_prog = CpDbMapper.sorties_to_aircraft_progression(sorties)

            return {
                "pilot": pilot_data,
                "missions": missions_data,
                "squadron": squadron_data,
                "aces": aces_data,
                "aircraft_progression": aircraft_prog,
            }
        except Exception:
            logger.exception("cp.db: falha ao processar carreira '%s'", career_id_str)
            return {}

    def _enrich_latest_mission_with_flight_log(self, missions: List[Dict[str, Any]]) -> None:
        if not missions:
            return

        summary = self._mission_report_reader.build_latest_report_summary()
        if not summary:
            return

        latest = missions[-1]
        current_description = str(latest.get("description", "") or "").strip()
        flight_log_block = "[FlightLogs]\n" + summary

        if flight_log_block not in current_description:
            latest["description"] = (
                f"{current_description}\n\n{flight_log_block}"
                if current_description
                else flight_log_block
            )

        latest["haReport"] = summary

    def get_earned_medal_ids(self, career_id_str: str) -> set:
        """Retorna set de IDs de medalhas conquistadas."""
        try:
            career_id = int(career_id_str) if career_id_str.isdigit() else None
            career = self._reader.get_active_career(career_id)
            if not career:
                return set()
            awards = self._reader.get_awards(int(career["id"]))
            return CpDbMapper.awards_to_earned_ids(awards)
        except Exception:
            logger.exception("cp.db: falha ao obter medalhas")
            return set()

    def close(self) -> None:
        self._reader.close()

    def __enter__(self) -> "CpDbCampaignRepository":
        self._reader.open()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

