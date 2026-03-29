from wingmate.analytics.reports.reports import PilotPerformanceReport
from wingmate.domain.entities.pilot import Pilot


class PilotAnalyticsEngine:
    def analyze(self, pilot: Pilot) -> PilotPerformanceReport:
        metrics = {
            "victories": pilot.victories,
            "missions_flown": pilot.missions_flown,
            "kill_ratio": pilot.kill_ratio,
        }
        return PilotPerformanceReport(pilot_id=pilot.pilot_id, metrics=metrics)
