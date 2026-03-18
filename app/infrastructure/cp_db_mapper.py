# -*- coding: utf-8 -*-
"""
Wing Mate — app/infrastructure/cp_db_mapper.py

Traduz rows brutas do cp.db para dicts no formato esperado pelos
ViewModels e serviços de aplicação existentes.

Convenções de mapeamento
------------------------
Tabela      → Modelo Wing Mate
----------    -------------------------
career      → Campaign (core.repositories)
pilot       → dict "pilot" (data_processor)
sortie      → dict "mission" (data_processor)
award       → dict "earned medal id" (MedalsTab / ProfileTab)
pilot.*     → dict "squadron member" (SquadronTab)
ace         → dict "ace" (AcesTab)

Códigos enumerados (engenharia reversa parcial do relatório forense)
--------------------------------------------------------------------
pilot.status:   0=Ativo, 1=Ativo, 2=KIA, 3=WIA, 4=POW, 5=MIA
sortie.status:  0=Normal, 1=KIA, 2=WIA, 3=POW, 4=MIA
award.type:     inteiro → prefixo "award_<type>"  (mapeamento expansível)
event.type:     1=Promoção, 2=Morte, 3=Ferido, … (parcialmente conhecido)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from app.core.country_normalizer import canonicalize_country_code
from app.core.rank_registry import resolve_rank

logger = logging.getLogger("IL2CampaignAnalyzer")


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _safe_str(v: Any, fallback: str = "N/A") -> str:
    return str(v).strip() if v is not None else fallback


def _safe_int(v: Any, fallback: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return fallback


def _fmt_date(raw: Any) -> str:
    """Converte datetime SQLite (vários formatos) para DD/MM/YYYY."""
    if raw is None:
        return "N/A"
    s = str(raw).strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y",
    ):
        try:
            return datetime.strptime(s, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return s


def _fmt_time(raw: Any) -> str:
    """Extrai HH:MM de um datetime SQLite."""
    if raw is None:
        return ""
    s = str(raw).strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y.%m.%d %H:%M:%S",
        "%d.%m.%Y %H:%M:%S",
        "%H:%M:%S",
        "%H:%M",
    ):
        try:
            return datetime.strptime(s, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return ""


def _normalize_country(raw_country: Any) -> str:
    return canonicalize_country_code(raw_country)


def _clean_aircraft_name(raw_value: Any) -> str:
    text = str(raw_value or "").strip().strip('"')
    if not text:
        return "N/A"

    normalized = text.replace("\\", "/")
    if "/" in normalized:
        normalized = normalized.rsplit("/", 1)[-1]

    if normalized.lower().endswith(".txt"):
        normalized = normalized[:-4]

    normalized = normalized.replace("_", " ").replace("-", " ").strip()
    return normalized or "N/A"


def _normalize_person_name(raw_name: Any) -> str:
    return str(raw_name or "").strip().casefold()


# ------------------------------------------------------------------ #
# Mapeamento de status                                                 #
# ------------------------------------------------------------------ #

_PILOT_STATUS: Dict[int, str] = {
    0: "Ativo",
    1: "Ativo",
    2: "Morto em Combate (KIA)",
    3: "Gravemente Ferido (WIA)",
    4: "Capturado (POW)",
    5: "Desaparecido em Combate (MIA)",
}

_SORTIE_STATUS: Dict[int, str] = {
    0: "Retornou",
    1: "Morto em Combate (KIA)",
    2: "Gravemente Ferido (WIA)",
    3: "Capturado (POW)",
    4: "Desaparecido em Combate (MIA)",
}

# Prefixo de ID de medalha por tipo (expansível conforme os tipos forem decifrados)
_AWARD_TYPE_ID: Dict[int, str] = {
    0: "award_generic",
    1: "iron_cross_1st",
    2: "iron_cross_2nd",
    3: "pour_le_merite",
    4: "wound_badge",
    5: "pilot_badge",
    6: "hohenzollern",
}


def _pilot_status_str(code: int) -> str:
    return _PILOT_STATUS.get(code, "Desconhecido")


def _sortie_status_str(code: int) -> str:
    return _SORTIE_STATUS.get(code, "Desconhecido")


def _award_medal_id(award_type: int) -> str:
    return _AWARD_TYPE_ID.get(award_type, f"award_{award_type}")


# ------------------------------------------------------------------ #
# Soma de kills de uma row                                             #
# ------------------------------------------------------------------ #

# Colunas de kill de aeronaves confirmadas no schema SQLite (pilot/sortie)
_KILL_COLS = (
    "killLightPlane", "killLightFighter", "killMediumPlane", "killMediumFighter",
    "killHeavyPlane", "killHeavyFighter",
    "killLightAttackPlane", "killMediumAttackPlane", "killHeavyAttackPlane",
    "killLightBomber", "killMediumBomber", "killHeavyBomber",
    "killLightRecon", "killMediumRecon", "killHeavyRecon",
    "killStaticPlane",
)


def _sum_plane_kills(row: Dict[str, Any]) -> int:
    total_kills = 0
    for col in _KILL_COLS:
        total_kills += _safe_int(row.get(col))
    return total_kills


def _compute_morale_from_sorties(sorties: List[Dict[str, Any]]) -> int:
    """Deriva a moral do piloto a partir das últimas 5 sorties."""
    recent = sorties[-5:] if len(sorties) > 5 else sorties
    morale = 50
    for sortie in recent:
        status = _safe_int(sortie.get("status"))
        kills = _sum_plane_kills(sortie)
        if status == 1:
            morale -= 25
        elif status == 0 and kills > 0:
            morale += 10
    return max(0, min(100, morale))


def _morale_mood_icon(morale: int) -> str:
    """Retorna ícone de humor idêntico ao de IL2DataProcessor.morale_mood_icon()."""
    if morale < 20:
        return "😵 Exausto"
    if morale < 50:
        return "😟 Abalado"
    if morale <= 80:
        return "😐 Estável"
    return "🔥 Inspirado"


def fmt_flight_time(seconds: int) -> str:
    total_seconds = max(0, _safe_int(seconds, 0))
    total_minutes = total_seconds // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


# ------------------------------------------------------------------ #
# Mappers públicos                                                     #
# ------------------------------------------------------------------ #

class CpDbMapper:
    """Converte dicts brutos do CpDbReader em objetos do domínio Wing Mate."""

    # ---------- career → Campaign dict ---------- #

    @staticmethod
    def career_to_campaign_dict(
        career: Dict[str, Any],
        personage: Optional[Dict[str, Any]],
        pilot: Optional[Dict[str, Any]],
        squadron: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Retorna um dict compatível com o que JsonCampaignRepository.get_campaign() produz.
        """
        player_name = "N/A"
        if pilot:
            player_name = _safe_str(pilot.get("name"))
        elif personage:
            player_name = _safe_str(personage.get("nickName") or personage.get("firstName"))

        squad_name = "N/A"
        if squadron:
            squad_name = _safe_str(
                squadron.get("name") or squadron.get("airfield", "Esquadrão desconhecido")
            )

        return {
            "name": str(career.get("id", "")),   # usa id como "nome" de campanha
            "player_serial": str(career.get("personageId", "")),
            "squadron_name": squad_name,
            "reference_date": _safe_str(career.get("currentDate"), ""),
            # extras úteis
            "iron_man": bool(_safe_int(career.get("ironMan"))),
            "start_date": _safe_str(career.get("startDate"), ""),
            "tvd": _safe_int(career.get("tvd")),
            "pilot_name": player_name,
        }

    # ---------- pilot rows → pilot stats dict ---------- #

    @staticmethod
    def pilot_to_pilot_data(
        pilot: dict,
        sorties: list,
        squad_name: str = "N/A",
    ) -> dict:
        """
        Produz o dict "pilot" consumido por ProfileTab / MainWindow._update_profile_from_data().

        Regras de negócio alinhadas com IL2DataProcessor.process_pilot_data():
          - XP base   = (missões×100) + (vitórias×500) + (sobrevivências×200)
          - XP final  = round(xp_base × (1.2 se morale > 80 senão 1.0))
          - Moral     = derivada das últimas 5 sorties via _compute_morale_from_sorties()
          - Exausto   = morale < 20
        """
        total_victories = _sum_plane_kills(pilot)
        total_missions = len(sorties)
        survival_count = sum(
            1 for sortie in sorties if _safe_int(sortie.get("status")) == 0
        )
        flight_time_s = sum(_safe_int(sortie.get("flightTime")) for sortie in sorties)

        xp_base = (total_missions * 100) + (total_victories * 500) + (survival_count * 200)

        morale = _compute_morale_from_sorties(sorties)
        xp_multiplier = 1.2 if morale > 80 else 1.0
        xp = int(round(xp_base * xp_multiplier))
        exhausted = morale < 20

        country = _normalize_country(pilot.get("country"))
        rank_id = _safe_int(pilot.get("rankId"))

        return {
            "name": _safe_str(pilot.get("name")),
            "squadron": squad_name,
            "total_missions": total_missions,
            "total_victories": total_victories,
            "survival_count": survival_count,
            "flight_time_minutes": flight_time_s // 60,
            "flight_time_formatted": fmt_flight_time(flight_time_s),
            "xp": xp,
            "xp_base": xp_base,
            "xp_multiplier": xp_multiplier,
            "morale": morale,
            "morale_state": "Exausto" if exhausted else "Ativo",
            "morale_mood": _morale_mood_icon(morale),
            "needs_rest": exhausted,
            "rank_id": rank_id,
            "rank": resolve_rank(country, rank_id),
            "country": country,
        }

    # ---------- sortie rows → mission dicts ---------- #

    @staticmethod
    def sorties_to_missions(
        sorties: List[Dict[str, Any]],
        missions_by_id: Dict[int, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Produz lista de dicts "mission" compatível com MissionValidationService.validate().
        """
        out: List[Dict[str, Any]] = []
        for s in sorties:
            mission_id = _safe_int(s.get("missionId"), -1)
            mission_row = missions_by_id.get(mission_id, {})

            date_raw = s.get("date") or mission_row.get("date")
            aircraft = _clean_aircraft_name(
                s.get("model")
                or s.get("name")
                or mission_row.get("plane")
                or mission_row.get("playerPlane")
                or mission_row.get("aircraft")
            )
            victories = _sum_plane_kills(s)
            status_code = _safe_int(s.get("status"))
            status_str = _sortie_status_str(status_code)

            # Badge progressivo igual à lógica do data_processor
            all_sorties_same_plane = [
                x for x in sorties if (x.get("model") or x.get("name")) == aircraft
            ]
            plane_victories = sum(_sum_plane_kills(x) for x in all_sorties_same_plane)
            if plane_victories >= 5:
                badge = "Ás do Modelo"
            elif len(all_sorties_same_plane) <= 5:
                badge = "Novato"
            else:
                badge = "Veterano"

            airfield = _safe_str(mission_row.get("airfield"), "N/A")
            duty = _safe_str(
                mission_row.get("type")
                or mission_row.get("task")
                or mission_row.get("name")
                or "Missão",
                "Missão",
            )
            description = (
                f"Missão em {_fmt_date(date_raw)} {_fmt_time(date_raw)} — {aircraft}. "
                f"Tipo: {duty}. "
                f"Status: {status_str}. "
                f"Abates aéreos: {victories}. "
                f"Aeródromo: {airfield}."
            )

            out.append({
                "date": _fmt_date(date_raw),
                "time": _fmt_time(date_raw),
                "aircraft": aircraft,
                "aircraft_badge": badge,
                "duty": duty,
                "locality": airfield,
                "airfield": airfield,
                "pilots": [],
                "pilots_in_mission": [],
                "weather": "Não disponível",
                "description": description,
                "haReport": "",
                # metadata extra
                "victories": victories,
                "status": status_code,
                "status_text": status_str,
                "score": _safe_int(s.get("score")),
                "flight_time_s": _safe_int(s.get("flightTime")),
                "source": "vanilla_db",
                "flight_time_formatted": fmt_flight_time(_safe_int(s.get("flightTime"))),
            })
        return out

    # ---------- pilot rows → squadron member dicts ---------- #

    @staticmethod
    def pilots_to_squadron(pilots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Produz lista de dicts de membros compatível com SquadronTab.set_squadron().
        """
        out: List[Dict[str, Any]] = []
        for p in pilots:
            victories = _sum_plane_kills(p)
            missions = _safe_int(p.get("sortiesNum") or p.get("sorties"), 0)
            status_code = _safe_int(p.get("status"))

            out.append({
                "name": _safe_str(p.get("name")),
                "rank": _safe_str(p.get("rank"), "N/A"),
                "victories": victories,
                "missions_flown": missions,
                "status": _pilot_status_str(status_code),
            })

        out.sort(key=lambda x: (x["missions_flown"], x["victories"]), reverse=True)
        return out

    # ---------- award rows → earned medal ids ---------- #

    @staticmethod
    def awards_to_earned_ids(awards: List[Dict[str, Any]]) -> Set[str]:
        """
        Retorna set de medal IDs compatível com MedalsTab.set_earned_ids().
        """
        ids: Set[str] = set()
        for a in awards:
            award_type = _safe_int(a.get("type"))
            ids.add(_award_medal_id(award_type))
        return ids

    # ---------- ace rows → ace dicts ---------- #

    @staticmethod
    def aces_to_aces_data(
        aces: List[Dict[str, Any]],
        pilots_by_id: Optional[Dict[Any, Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Produz lista de dicts de ases compatível com AcesTab.set_aces().
        Tenta enriquecer com dados de pilot (victories, rank) se disponível.
        """
        out: List[Dict[str, Any]] = []
        pb = pilots_by_id or {}
        for ace in aces:
            pilot: Dict[str, Any] = {}
            if pb:
                pilot = pb.get(_safe_int(ace.get("pilotId")), {})
                if not pilot:
                    pilot = pb.get(_normalize_person_name(ace.get("name")), {})
            victories = _safe_int(ace.get("victories"), -1)
            if victories < 0:
                victories = _sum_plane_kills(pilot) if pilot else 0
            out.append({
                "name": _safe_str(ace.get("name")),
                "rank": _safe_str(ace.get("rank") or pilot.get("rank"), "N/A"),
                "country": _normalize_country(ace.get("country") or pilot.get("country")),
                "victories": victories,
                "missions_flown": _safe_int(ace.get("sortiesNum") or pilot.get("sortiesNum"), 0),
            })
        out.sort(key=lambda x: x["victories"], reverse=True)
        return out

    # ---------- career → aircraft progression ---------- #

    @staticmethod
    def sorties_to_aircraft_progression(
        sorties: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Reconstrói o dict aircraft_progression no formato do data_processor.
        """
        prog: Dict[str, Dict[str, Any]] = {}
        for s in sorties:
            model = _safe_str(s.get("model") or s.get("name"), "N/A")
            stats = prog.setdefault(model, {"missions": 0, "confirmed_victories": 0, "badge": "Novato"})
            stats["missions"] += 1
            stats["confirmed_victories"] += _sum_plane_kills(s)
            v = stats["confirmed_victories"]
            m = stats["missions"]
            if v >= 5:
                stats["badge"] = "Ás do Modelo"
            elif m <= 5:
                stats["badge"] = "Novato"
            else:
                stats["badge"] = "Veterano"
        return prog
