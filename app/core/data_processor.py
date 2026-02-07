# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/core/data_processor.py
# Processador de dados das campanhas IL-2
# ===================================================================

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Tuple

logger = logging.getLogger("IL2CampaignAnalyzer")

try:
    from .data_parser import IL2DataParser  # pacote
except ImportError:
    try:
        from core.data_parser import IL2DataParser  # pacote absoluto
    except ImportError:
        from data_parser import IL2DataParser  # plano


class IL2DataProcessor:
    """Processador de dados das campanhas IL-2."""
    
    def __init__(self, pwcgfc_path: Union[str, Path, None] = None) -> None:
        """
        Inicializa o processador.
        
        Args:
            pwcgfc_path: Caminho para o diretório PWCGFC
        """
        self.parser = IL2DataParser(pwcgfc_path)

    def process_campaign(self, campaign_name: str) -> Dict[str, Any]:
        """
        Processa todos os dados de uma campanha.
        
        Args:
            campaign_name: Nome da campanha
            
        Returns:
            Dicionário com dados processados da campanha
        """
        campaign_info = self.parser.get_campaign_info(campaign_name)
        if not campaign_info:
            return {}

        player_serial = str(campaign_info.get("referencePlayerSerialNumber", ""))
        combat_reports = self.parser.get_combat_reports(campaign_name, player_serial)

        # Processa missões
        missions_data: List[Dict[str, Any]]
        player_squadron_id: Optional[int]
        missions_data, player_squadron_id = self.process_missions_data(
            campaign_name, combat_reports, player_serial
        )

        # Processa dados do piloto
        pilot_data: Dict[str, Any] = self.process_pilot_data(campaign_info, combat_reports)

        # Processa squadron
        if player_squadron_id:
            squadron_personnel = self.parser.get_squadron_personnel(
                campaign_name, player_squadron_id
            )
            squadron_data: List[Dict[str, Any]] = self.process_squadron_data(squadron_personnel)
        else:
            squadron_data: List[Dict[str, Any]] = []

        # Processa ases (mantém rank e country)
        aces_data: List[Dict[str, Any]] = self.process_aces_data(
            self.parser.get_campaign_aces(campaign_name)
        )

        return {
            "pilot": pilot_data,
            "missions": missions_data,
            "squadron": squadron_data,
            "aces": aces_data,
        }

    def process_missions_data(
        self, campaign_name: str, combat_reports: List[Dict[str, Any]], player_serial: str
    ) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        """
        Processa dados das missões.
        
        Args:
            campaign_name: Nome da campanha
            combat_reports: Lista de relatórios de combate
            player_serial: Serial do jogador
            
        Returns:
            Tupla com (lista de missões, ID do squadron do jogador)
        """
        missions_with_key: List[Tuple[str, Dict[str, Any]]] = []
        player_squadron_id: Optional[int] = None

        for report in combat_reports:
            if not isinstance(report, dict):
                continue

            raw_date = str(report.get("date", ""))

            try:
                mission_details: Dict[str, Any] = (
                    self.parser.get_mission_data(campaign_name, report) or {}
                )
            except (KeyError, TypeError, ValueError, OSError):
                mission_details = {}

            mission_time = str(report.get("time", "NA"))
            pilots_in_mission: List[str] = []
            ha_report = str(report.get("haReport") or "")

            if ha_report:
                try:
                    for line in re.findall(r"^.+$", ha_report, re.MULTILINE):
                        clean = str(line).strip()
                        if clean and not clean.lower().startswith(("this mission", "the mission")):
                            pilots_in_mission.append(clean)
                except re.error:
                    logger.warning(f"Erro de regex ao processar haReport: {ha_report[:50]}...")

            weather_text = str("Não disponível")
            description_text = str(
                mission_details.get("missionDescription", "Descrição da missão não encontrada.")
                if mission_details
                else "Descrição da missão não encontrada."
            )

            try:
                if mission_details:
                    # Busca Weather Report na descrição
                    match: Optional[re.Match] = re.search(
                        r"(Weather Report.*?)$", description_text, re.DOTALL | re.IGNORECASE
                    )
                    if match:
                        weather_text = match.group(1).strip()

                if not player_squadron_id:
                    mission_planes: Dict[str, Any] = mission_details.get("missionPlanes", {}) or {}
                    for k, v in mission_planes.items():
                        try:
                            if str(k) == str(player_serial):
                                player_squadron_id = (
                                    v.get("squadronId") if isinstance(v, dict) else None
                                )
                                break
                        except (TypeError, AttributeError):
                            continue
            except (AttributeError, TypeError):
                pass

            mission_entry: Dict[str, Any] = {
                "date": self.format_date(raw_date) if raw_date else report.get("date", "NA"),
                "time": mission_time,
                "aircraft": report.get("type", "NA"),
                "duty": report.get("duty", "NA"),
                "locality": report.get("locality", "NA"),
                "airfield": (
                    mission_details.get("missionHeader", {}).get("airfield", "NA")
                    if isinstance(mission_details.get("missionHeader", {}), dict)
                    else "NA"
                ),
                "pilots": pilots_in_mission,
                "weather": weather_text,
                "description": description_text,
                "haReport": report.get("haReport", ""),
            }

            missions_with_key.append((raw_date or "99999999", mission_entry))

        try:
            missions_with_key.sort(key=lambda t: (t[0] or "99999999", t[0]))
        except (TypeError, ValueError):
            pass

        missions: List[Dict[str, Any]] = [m for _, m in missions_with_key]
        return missions, player_squadron_id

    def process_squadron_data(self, squadron_personnel: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Processa dados do squadron.
        
        Args:
            squadron_personnel: Dados do pessoal do squadron
            
        Returns:
            Lista de dicionários com dados dos membros do squadron
        """
        result: List[Dict[str, Any]] = []
        if not squadron_personnel:
            return result

        coll: Dict[str, Any] = squadron_personnel.get("squadronMemberCollection", {}) or {}

        for p in coll.values():
            try:
                victories: Any = p.get("victories", [])
                v_count = (
                    int(len(victories))
                    if isinstance(victories, (list, tuple, dict))
                    else int(victories)
                    if str(victories).isdigit()
                    else 0
                )
            except (TypeError, ValueError):
                v_count = 0

            try:
                m_flown: Any = p.get("missionFlown", 0)
                m_flown = (
                    int(m_flown)
                    if isinstance(m_flown, int)
                    else int(m_flown)
                    if str(m_flown).isdigit()
                    else 0
                )
            except (TypeError, ValueError):
                m_flown = 0

            result.append(
                {
                    "name": p.get("name", "NA"),
                    "rank": p.get("rank", "NA"),
                    "victories": v_count,
                    "missions_flown": m_flown,
                    "status": self.get_pilot_status(p.get("pilotActiveStatus", -1)),
                }
            )

        result.sort(key=lambda x: (x["missions_flown"], x["victories"]), reverse=True)
        return result

    def get_pilot_status(self, code: int) -> str:
        """
        Traduz código de status do piloto.
        
        Args:
            code: Código de status
            
        Returns:
            Descrição do status
        """
        return {
            0: "Ativo",
            1: "Ativo",
            2: "Morto em Combate (KIA)",
            3: "Gravemente Ferido (WIA)",
            4: "Capturado (POW)",
            5: "Desaparecido em Combate (MIA)",
        }.get(code, "Desconhecido")

    def process_aces_data(self, aces_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processa dados de ases mantendo TODOS os campos importantes.
        
        Args:
            aces_raw: Lista de dicionários com dados brutos dos ases
            
        Returns:
            Lista de dicionários com dados processados dos ases
        """
        out: List[Dict[str, Any]] = []
        if not aces_raw:
            return out

        for ace in aces_raw:
            try:
                # Conta vitórias (é um array no JSON)
                v: Any = ace.get("victories", [])
                v_count = (
                    int(len(v))
                    if isinstance(v, list)
                    else int(v)
                    if isinstance(v, (int, str)) and str(v).isdigit()
                    else 0
                )
            except (TypeError, ValueError):
                v_count = 0

            # Mantém TODOS os campos importantes
            out.append({
                "name": ace.get("name", "NA"),
                "rank": ace.get("rank", "NA"),
                "country": ace.get("country", ""),
                "victories": v_count,
                "missions_flown": ace.get("missionFlown", 0),
            })

        out.sort(key=lambda x: x["victories"], reverse=True)
        return out

    def format_date(self, yyyymmdd: str) -> str:
        """
        Formata data de YYYYMMDD para DD/MM/YYYY.
        
        Args:
            yyyymmdd: Data no formato YYYYMMDD
            
        Returns:
            Data formatada ou original se inválida
        """
        if not yyyymmdd or len(yyyymmdd) != 8 or not yyyymmdd.isdigit():
            return yyyymmdd
        try:
            return datetime.strptime(yyyymmdd, "%Y%m%d").strftime("%d/%m/%Y")
        except ValueError:
            return yyyymmdd

    def process_pilot_data(
        self, campaign_info: Dict[str, Any], combat_reports: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Processa dados do piloto.
        
        Args:
            campaign_info: Informações da campanha
            combat_reports: Relatórios de combate
            
        Returns:
            Dicionário com dados do piloto
        """
        pilot: Dict[str, Any] = {}
        try:
            pilot_name = (
                campaign_info.get("referencePlayerName")
                or campaign_info.get("playerName")
                or campaign_info.get("name")
                or "NA"
            )

            squadron_name: Optional[str] = (
                campaign_info.get("referencePlayerSquadronName")
                or campaign_info.get("playerSquadron")
            )

            if not squadron_name:
                for r in combat_reports:
                    if isinstance(r, dict) and r.get("squadron"):
                        squadron_name = r.get("squadron")
                        break

            pilot_squadron = squadron_name or "NA"
            pilot_total_missions = len([r for r in combat_reports if isinstance(r, dict)])

        except (AttributeError, TypeError):
            pilot.setdefault("name", "NA")
            pilot.setdefault("squadron", "NA")
            pilot.setdefault("total_missions", 0)
            return pilot

        return {
            "name": pilot_name,
            "squadron": pilot_squadron,
            "total_missions": pilot_total_missions,
        }
