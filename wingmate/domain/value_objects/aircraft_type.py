from dataclasses import dataclass


@dataclass(frozen=True)
class AircraftType:
    code: str
    name: str
