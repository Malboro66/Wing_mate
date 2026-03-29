from wingmate.application.dto.campaign_dto import CampaignDTO
from wingmate.domain.repositories.campaign_repository import CampaignRepository


class LoadCampaign:
    def __init__(self, campaign_repository: CampaignRepository) -> None:
        self._campaign_repository = campaign_repository

    def execute(self, campaign_id: str) -> CampaignDTO:
        campaign = self._campaign_repository.load_campaign(campaign_id)
        return CampaignDTO(campaign_id=campaign.campaign_id, name=campaign.name, missions=len(campaign.missions))
