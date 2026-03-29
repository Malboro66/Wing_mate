from wingmate.domain.entities.mission import Mission


class MissionMapper:
    def map(self, payload: dict) -> Mission:
        return Mission(mission_id=str(payload.get("mission_id", "unknown")), date=str(payload.get("date", "")))
