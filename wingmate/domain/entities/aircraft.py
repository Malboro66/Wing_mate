from dataclasses import dataclass

from wingmate.domain.value_objects.aircraft_type import AircraftType


@dataclass
class Aircraft:
    aircraft_id: str
    aircraft_type: AircraftType
    total_sorties: int = 0
    total_kills: int = 0
