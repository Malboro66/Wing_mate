from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple

from app.core.batch_repository import JsonBatchRepository
from app.core.data_parser import IL2DataParser

logger = logging.getLogger("IL2CampaignAnalyzer")


@dataclass(frozen=True)
class PersonnelResolutionResult:
    country_code: str
    display_name: str
    earned_medal_ids: FrozenSet[str]


class PersonnelResolutionService:
    """Resolve país e medalhas do piloto a partir dos arquivos Personnel."""

    def __init__(self, parser_provider: Callable[[], IL2DataParser]) -> None:
        self._parser_provider = parser_provider

    def resolve(self, campaign: str, pilot_name: str) -> PersonnelResolutionResult:
        pilot_name_norm = (pilot_name or "").strip().lower()
        campaign_norm = (campaign or "").strip()
        default = PersonnelResolutionResult("GERMANY", "Germany", frozenset())

        if not pilot_name_norm or not campaign_norm:
            return default

        parser = self._parser_provider()
        personnel_dir: Path = parser.campaigns_path / campaign_norm / "Personnel"
        if not personnel_dir.exists():
            logger.warning("Diretório Personnel não encontrado: %s", personnel_dir)
            return default

        earned_ids = set()
        resolved_code = default.country_code
        display_name = default.display_name

        try:
            personnel_files = sorted(personnel_dir.glob("*.json"))
            batch_repo = JsonBatchRepository(parser)
            loaded_payloads, stats = batch_repo.load_many(personnel_files)
            logger.info(
                "Batch Personnel: %s solicitados, %s carregados",
                stats.requested,
                stats.loaded,
            )

            def _resolve_member(_path: Path, payload: Any) -> Optional[Tuple[str, str, List[Dict[str, Any]]]]:
                if not isinstance(payload, dict):
                    return None
                coll: Dict[str, Any] = payload.get("squadronMemberCollection", {}) or {}
                for member in coll.values():
                    try:
                        name = str(member.get("name", "") or "").strip().lower()
                        if name != pilot_name_norm:
                            continue
                        country = str(member.get("country", "") or "").strip().upper()
                        medals: List[Dict[str, Any]] = member.get("medals", []) or []
                        return country, name, medals
                    except (KeyError, TypeError, AttributeError):
                        continue
                return None

            matches = batch_repo.resolve_many(loaded_payloads, _resolve_member)
            if matches:
                country, _, medals = matches[0]
                resolved_code, display_name = self._map_country_to_folder_and_label(country)
                for medal in medals:
                    img = str(medal.get("medalImage", "") or "").strip()
                    if img:
                        medal_id = img[:-4] if img.lower().endswith(".png") else img
                        earned_ids.add(medal_id)
                        continue

                    medal_name = str(medal.get("medalName", "") or "").strip()
                    if medal_name:
                        earned_ids.add(medal_name.lower().replace(" ", "_"))

                logger.info("Resolvido: país=%s, %s medalhas", resolved_code, len(earned_ids))
                return PersonnelResolutionResult(
                    country_code=resolved_code,
                    display_name=display_name,
                    earned_medal_ids=frozenset(earned_ids),
                )
        except OSError:
            logger.exception("Falha ao varrer diretório Personnel: %s", personnel_dir)
        except Exception:
            logger.exception("Falha inesperada ao resolver país/medalhas")

        return PersonnelResolutionResult(
            country_code=resolved_code,
            display_name=display_name,
            earned_medal_ids=frozenset(earned_ids),
        )

    @staticmethod
    def _map_country_to_folder_and_label(country: str) -> tuple[str, str]:
        c = (country or "").strip().upper()
        if c in ("GERMANY", "GER", "DE", "DEU", "ALEMANHA", "ALLEMAGNE", "DEUTSCHLAND"):
            return ("GERMANY", "Germany")
        if c in ("FRANCE", "FR", "FRA"):
            return ("FRANCE", "France")
        if c in ("BRITAIN", "UK", "GB", "GBR", "UNITED KINGDOM", "BRIT"):
            return ("BRITAIN", "Britain")
        if c in ("BELGIAN", "BELGIUM", "BE", "BEL"):
            return ("BELGIAN", "Belgian")
        if c in ("USA", "US", "UNITED STATES", "UNITED STATES OF AMERICA"):
            return ("USA", "USA")
        return ("GERMANY", "Germany")
