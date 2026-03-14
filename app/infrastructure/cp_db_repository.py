# -*- coding: utf-8 -*-
"""
Wing Mate Ã¢â‚¬â€ app/infrastructure/cp_db_repository.py

ImplementaÃƒÂ§ÃƒÂ£o concreta de CampaignRepositoryPort que lÃƒÂª dados do cp.db.

Uso:
    from app.infrastructure.cp_db_repository import CpDbCampaignRepository
    repo = CpDbCampaignRepository(Path("/path/to/cp.db"))
    campaign = repo.get_campaign("1")          # id como string
    missions  = repo.get_missions("1", "abc")  # ignora serial no modo db
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.repositories import Campaign, CampaignRepositoryPort
from app.infrastructure.cp_db_mapper import CpDbMapper
from app.infrastructure.cp_db_reader import CpDbReader
from app.infrastructure.vanilla_mission_report import VanillaMissionReportReader
from app.infrastructure.vanilla_squadron_catalog import VanillaSquadronCatalog

logger = logging.getLogger("IL2CampaignAnalyzer")


class CpDbCampaignRepository:
    """Implementa CampaignRepositoryPort sobre o banco SQLite cp.db."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._reader = CpDbReader(db_path)
        self._mapper = CpDbMapper()
        self._mission_report_reader = VanillaMissionReportReader(db_path)
        self._squadron_catalog = VanillaSquadronCatalog(db_path)

    # ------------------------------------------------------------------ #
    # CampaignRepositoryPort                                               #
    # ------------------------------------------------------------------ #

    def get_campaign(self, name: str) -> Optional[Campaign]:
        """
        name: pode ser o id numÃƒÂ©rico da carreira (como string)
              ou "active" para buscar a carreira ativa.
        """
        try:
            career_id: Optional[int] = None
            selected_id = self.extract_career_id(name)
            if selected_id.isdigit():
                career_id = int(selected_id)

            career = self._reader.get_active_career(career_id)
            if not career:
                logger.warning("cp.db: carreira '%s' nÃƒÂ£o encontrada", name)
                return None

            personage_id = str(career.get("personageId", ""))
            personage = self._reader.get_personage(personage_id) if personage_id else None
            pilot = self._reader.get_player_pilot(personage_id) if personage_id else None
            squadron = self._reader.get_squadron(int(career.get("squadronId", -1)))
            squadron_name = self._resolve_squadron_name(int(career.get("id", -1)), squadron)
            if squadron is not None:
                squadron = dict(squadron)
                squadron["name"] = squadron_name

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
        Retorna lista de dicts de missÃƒÂµes no formato esperado pelos ViewModels.
        serial: ignorado (no db, o vÃƒÂ­nculo ÃƒÂ© via careerId / personageId).
        """
        try:
            selected_id = self.extract_career_id(campaign_name)
            career_id = int(selected_id) if selected_id.isdigit() else None
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

            # ÃƒÂndice de missions por id para enriquecer cada sortie
            missions_list = self._reader.get_missions(career_id)
            missions_by_id: Dict[int, Dict[str, Any]] = {
                int(m["id"]): m for m in missions_list
            }

            missions_data = CpDbMapper.sorties_to_missions(sorties, missions_by_id)
            self._enrich_missions_with_flight_logs(missions_data)
            return missions_data
        except Exception:
            logger.exception("cp.db: falha ao obter missÃƒÂµes da carreira '%s'", campaign_name)
            return []

    # ------------------------------------------------------------------ #
    # MÃƒÂ©todos extras (nÃƒÂ£o exigidos pela porta, mas ÃƒÂºteis para MainWindow)  #
    # ------------------------------------------------------------------ #

    def list_career_ids(self) -> List[str]:
        """Lista IDs de carreiras disponÃƒÂ­veis (para popular o combo de campanhas)."""
        try:
            return [str(c["id"]) for c in self._reader.list_careers()]
        except Exception:
            logger.exception("cp.db: falha ao listar carreiras")
            return []

    def list_career_labels(self) -> Dict[str, str]:
        """Mapeia id de carreira para um rótulo amigável exibível no combo."""
        labels: Dict[str, str] = {}
        try:
            for c in self._reader.list_careers():
                career_id = str(c.get("id", "") or "").strip()
                if not career_id:
                    continue
                personage_id = str(c.get("personageId", "") or "")
                pilot = self._reader.get_player_pilot(personage_id) if personage_id else None
                pilot_name = str((pilot or {}).get("name", "") or "").strip()
                labels[career_id] = f"{career_id} - {pilot_name}" if pilot_name else career_id
        except Exception:
            logger.exception("cp.db: falha ao construir rótulos de carreira")
        return labels

    def process_career(self, career_id_str: str) -> Dict[str, Any]:
        """
        Equivalente ao IL2DataProcessor.process_campaign() mas para o banco.
        Retorna o mesmo dict esperado por MainWindow._on_data_loaded().
        """
        try:
            selected_id = self.extract_career_id(career_id_str)
            career_id = int(selected_id) if selected_id.isdigit() else None
            career = self._reader.get_active_career(career_id)
            if not career:
                return {}

            career_id = int(career["id"])
            personage_id = str(career.get("personageId", ""))
            pilot_row = self._reader.get_player_pilot(personage_id)
            squadron_row = self._reader.get_squadron(int(career.get("squadronId", -1)))
            all_pilots = self._reader.get_pilots(int(career.get("squadronId", -1)))
            pilots_lookup: Dict[Any, Dict[str, Any]] = {}
            for pilot in all_pilots:
                pilot_id = int(pilot.get("id", -1))
                if pilot_id >= 0:
                    pilots_lookup[pilot_id] = pilot
                normalized_name = str(pilot.get("name", "") or "").strip().casefold()
                if normalized_name:
                    pilots_lookup[normalized_name] = pilot
            sorties = self._reader.get_pilot_sorties(int(pilot_row["id"])) if pilot_row else []
            missions_list = self._reader.get_missions(career_id)
            missions_by_id = {int(m["id"]): m for m in missions_list}
            aces_list = self._reader.get_aces(career_id)

            squad_name = self._resolve_squadron_name(career_id, squadron_row)

            pilot_data = CpDbMapper.pilot_to_pilot_data(
                pilot_row or {}, sorties, squad_name
            )
            missions_data = CpDbMapper.sorties_to_missions(sorties, missions_by_id)
            self._enrich_missions_with_flight_logs(missions_data)
            squadron_data = CpDbMapper.pilots_to_squadron(all_pilots)
            aces_data = CpDbMapper.aces_to_aces_data(aces_list, pilots_lookup)
            if not aces_data:
                for pilot_row in all_pilots:
                    member = CpDbMapper.pilots_to_squadron([pilot_row])[0]
                    if int(member.get("victories", 0) or 0) < 5:
                        continue
                    aces_data.append({
                        "name": member.get("name", "N/A"),
                        "rank": member.get("rank", "N/A"),
                        "country": self._normalize_country(pilot_row.get("country")),
                        "victories": int(member.get("victories", 0) or 0),
                        "missions_flown": int(member.get("missions_flown", 0) or 0),
                    })
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

    @staticmethod
    def _as_int(value: Any, default: int = -1) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _resolve_squadron_name(
        self,
        career_id: int,
        squadron_row: Optional[Dict[str, Any]],
    ) -> str:
        if not squadron_row:
            return "N/A"

        squad_config_id = self._as_int(squadron_row.get("configId"), -1)
        squad_id = self._as_int(squadron_row.get("id"), -1)

        name_from_award = self._reader.get_latest_award_squad_name(
            career_id,
            squad_config_id=squad_config_id,
            squad_id=squad_id,
        )
        if name_from_award:
            return name_from_award

        name_from_gtp = self._squadron_catalog.get_name(squad_config_id)
        if name_from_gtp:
            return name_from_gtp

        fallback = str(squadron_row.get("name") or squadron_row.get("airfield") or "").strip()
        return fallback or "N/A"

    @staticmethod
    def _parse_mission_datetime(mission: Dict[str, Any]) -> Optional[datetime]:
        date_part = str(mission.get("date", "") or "").strip()
        time_part = str(mission.get("time", "") or "").strip()
        if not date_part:
            return None

        value = f"{date_part} {time_part}".strip()
        formats = (
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        )
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def _enrich_missions_with_flight_logs(self, missions: List[Dict[str, Any]]) -> None:
        if not missions:
            return

        summaries_by_dt = self._mission_report_reader.build_report_summaries_by_datetime()
        if not summaries_by_dt:
            # fallback legado para manter comportamento mínimo
            summary = self._mission_report_reader.build_latest_report_summary()
            if not summary:
                return
            latest = missions[-1]
            current_description = str(latest.get("description", "") or "").strip()
            flight_log_block = "[FlightLogs]\n" + summary
            if flight_log_block not in current_description:
                latest["description"] = (
                    f"{current_description}\n\n{flight_log_block}" if current_description else flight_log_block
                )
            latest["haReport"] = summary
            return

        reports_by_minute: Dict[datetime, str] = {}
        for report_dt, summary in summaries_by_dt.items():
            reports_by_minute[report_dt.replace(second=0, microsecond=0)] = summary

        matched_any = False
        for mission in missions:
            mission_dt = self._parse_mission_datetime(mission)
            if mission_dt is None:
                continue
            summary = reports_by_minute.get(mission_dt.replace(second=0, microsecond=0))
            if not summary:
                continue
            matched_any = True

            current_description = str(mission.get("description", "") or "").strip()
            flight_log_block = "[FlightLogs]\n" + summary
            if flight_log_block not in current_description:
                mission["description"] = (
                    f"{current_description}\n\n{flight_log_block}" if current_description else flight_log_block
                )
            mission["haReport"] = summary

        if not matched_any and summaries_by_dt:
            latest_report_dt = max(summaries_by_dt.keys())
            summary = summaries_by_dt[latest_report_dt]
            latest = missions[-1]
            current_description = str(latest.get("description", "") or "").strip()
            flight_log_block = "[FlightLogs]\n" + summary
            if flight_log_block not in current_description:
                latest["description"] = (
                    f"{current_description}\n\n{flight_log_block}" if current_description else flight_log_block
                )
            latest["haReport"] = summary

    def get_earned_medal_ids(self, career_id_str: str) -> set:
        """Retorna set de IDs de medalhas conquistadas."""
        try:
            selected_id = self.extract_career_id(career_id_str)
            career_id = int(selected_id) if selected_id.isdigit() else None
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

    @staticmethod
    def extract_career_id(raw_value: str) -> str:
        value = str(raw_value or "").strip()
        if value.isdigit():
            return value

        match = re.match(r"^(\d+)", value)
        if match:
            return match.group(1)
        return ""

    @staticmethod
    def _normalize_country(raw_country: Any) -> str:
        value = str(raw_country or "").strip().upper()
        if value in {"GER", "DE", "DEU", "GERMANY"}:
            return "GERMANY"
        if value in {"FRA", "FR", "FRANCE"}:
            return "FRANCE"
        if value in {"GB", "UK", "GBR", "BRITAIN"}:
            return "BRITAIN"
        if value in {"BEL", "BE", "BELGIUM", "BELGIAN"}:
            return "BELGIAN"
        if value in {"USA", "US", "UNITED STATES"}:
            return "USA"
        return value or "GERMANY"
