# core/repositories.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from .data_parser import IL2DataParser


@dataclass
class Campaign:
    name: str
    player_serial: str
    squadron_name: str
    reference_date: Optional[str] = None


class CampaignRepositoryPort(Protocol):
    """Porta de repositório para acesso a dados de campanha."""

    def get_campaign(self, name: str) -> Optional[Campaign]:
        ...

    def get_missions(self, campaign_name: str, serial: str) -> List[Dict[str, Any]]:
        ...


class JsonCampaignRepository:
    """Implementação concreta de repositório usando JSON local via IL2DataParser."""

    def __init__(self, parser: IL2DataParser):
        self._parser = parser

    def get_campaign(self, name: str) -> Optional[Campaign]:
        raw = self._parser.get_campaign_info(name)
        if not raw:
            return None
        return Campaign(
            name=name,
            player_serial=str(raw.get("referencePlayerSerialNumber", "")),
            squadron_name=raw.get("referencePlayerSquadronName", "N/A"),
            reference_date=raw.get("campaignDate"),
        )

    def get_missions(self, campaign_name: str, serial: str) -> List[Dict[str, Any]]:
        return self._parser.get_combat_reports(campaign_name, serial)


class CampaignRepository(JsonCampaignRepository):
    """Compatibilidade retroativa: mantém nome antigo apontando para implementação JSON."""

