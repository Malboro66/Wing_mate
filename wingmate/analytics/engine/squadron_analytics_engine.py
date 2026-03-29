from wingmate.analytics.reports.reports import SquadronPerformanceReport
from wingmate.domain.entities.squadron import Squadron


class SquadronAnalyticsEngine:
    def analyze(self, squadron: Squadron) -> SquadronPerformanceReport:
        metrics = {
            "member_count": len(squadron.members),
            "active_member_count": len(squadron.active_members()),
        }
        return SquadronPerformanceReport(squadron_id=squadron.squadron_id, metrics=metrics)
