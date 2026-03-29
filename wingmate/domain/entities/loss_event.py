from dataclasses import dataclass


@dataclass(frozen=True)
class LossEvent:
    pilot_id: str
    cause: str
    timestamp: str
