from wingmate.domain.entities.pilot import Pilot
from wingmate.domain.value_objects.pilot_rank import PilotRank


class PilotMapper:
    def map(self, payload: dict) -> Pilot:
        rank_name = str(payload.get("rank", "Unknown"))
        return Pilot(
            pilot_id=str(payload.get("pilot_id", "unknown")),
            name=str(payload.get("name", "Unknown")),
            rank=PilotRank(name=rank_name, order=0),
        )
