from wingmate.domain.entities.campaign import Campaign
from wingmate.domain.repositories.campaign_repository import CampaignRepository
from typing import Dict, List


class JsonCampaignRepository(CampaignRepository):
    def __init__(self) -> None:
        self._store: Dict[str, Campaign] = {}

    def load_campaign(self, campaign_id: str) -> Campaign:
        return self._store[campaign_id]

    def save_campaign(self, campaign: Campaign) -> None:
        self._store[campaign.campaign_id] = campaign

    def list_campaigns(self) -> List[str]:
        return sorted(self._store.keys())
