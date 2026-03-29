from wingmate.analytics.reports.reports import CampaignAnalyticsReport
from wingmate.domain.entities.campaign import Campaign


class CampaignAnalyticsEngine:
    def analyze(self, campaign: Campaign) -> CampaignAnalyticsReport:
        metrics = {
            "mission_count": len(campaign.missions),
            "squadron_count": len(campaign.squadrons),
        }
        return CampaignAnalyticsReport(campaign_id=campaign.campaign_id, metrics=metrics)
