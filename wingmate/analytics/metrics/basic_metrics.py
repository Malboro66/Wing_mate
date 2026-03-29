from dataclasses import dataclass


@dataclass(frozen=True)
class KillRatio:
    value: float


@dataclass(frozen=True)
class SurvivalRate:
    value: float


@dataclass(frozen=True)
class MissionSuccessRate:
    value: float


@dataclass(frozen=True)
class AircraftEfficiency:
    value: float
