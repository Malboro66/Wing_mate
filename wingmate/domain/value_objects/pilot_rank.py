from dataclasses import dataclass


@dataclass(frozen=True)
class PilotRank:
    name: str
    order: int
