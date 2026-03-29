from dataclasses import dataclass


@dataclass(frozen=True)
class KillEvent:
    attacker_pilot_id: str
    target_type: str
    timestamp: str
