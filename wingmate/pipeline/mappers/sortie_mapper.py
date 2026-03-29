from wingmate.domain.entities.sortie import Sortie


class SortieMapper:
    def map(self, payload: dict) -> Sortie:
        return Sortie(
            sortie_id=str(payload.get("sortie_id", "unknown")),
            mission_id=str(payload.get("mission_id", "unknown")),
            pilot_id=str(payload.get("pilot_id", "unknown")),
            aircraft_name=str(payload.get("aircraft_name", "")),
        )
