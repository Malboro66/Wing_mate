from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.repositories import Campaign, CampaignRepositoryPort


class CampaignQueryService:
    """Serviço de aplicação para consultas de campanha desacoplado da infraestrutura."""

    def __init__(self, repository: CampaignRepositoryPort) -> None:
        self._repository = repository

    def get_campaign(self, name: str) -> Optional[Campaign]:
        return self._repository.get_campaign(name)

    def get_campaign_missions(self, campaign_name: str) -> List[Dict[str, Any]]:
        campaign = self._repository.get_campaign(campaign_name)
        if not campaign:
            return []
        return self._repository.get_missions(campaign_name, campaign.player_serial)
