from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from wingmate.domain.entities.campaign import Campaign


class CampaignRepository(ABC):
    @abstractmethod
    def load_campaign(self, campaign_id: str) -> Campaign:
        raise NotImplementedError

    @abstractmethod
    def save_campaign(self, campaign: Campaign) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_campaigns(self) -> List[str]:
        raise NotImplementedError
