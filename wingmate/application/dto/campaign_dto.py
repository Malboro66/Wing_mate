from dataclasses import dataclass, field


@dataclass
class CampaignDTO:
    campaign_id: str
    name: str
    missions: int = 0
    metadata: dict = field(default_factory=dict)
