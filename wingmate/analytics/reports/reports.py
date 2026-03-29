from dataclasses import dataclass, field


@dataclass
class CampaignAnalyticsReport:
    campaign_id: str
    metrics: dict = field(default_factory=dict)


@dataclass
class SquadronPerformanceReport:
    squadron_id: str
    metrics: dict = field(default_factory=dict)


@dataclass
class PilotPerformanceReport:
    pilot_id: str
    metrics: dict = field(default_factory=dict)
