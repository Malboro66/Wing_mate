from wingmate.domain.entities.campaign import Campaign
from wingmate.domain.repositories.campaign_repository import CampaignRepository
from typing import List


class SQLiteCampaignRepository(CampaignRepository):
    def load_campaign(self, campaign_id: str) -> Campaign:
        raise NotImplementedError("SQLiteCampaignRepository adapter pending migration")

    def save_campaign(self, campaign: Campaign) -> None:
        raise NotImplementedError("SQLiteCampaignRepository adapter pending migration")

    def list_campaigns(self) -> List[str]:
        raise NotImplementedError("SQLiteCampaignRepository adapter pending migration")
