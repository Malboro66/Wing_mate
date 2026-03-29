from dataclasses import dataclass, field
from typing import List

from wingmate.domain.entities.kill_event import KillEvent
from wingmate.domain.entities.loss_event import LossEvent


@dataclass
class Sortie:
    sortie_id: str
    mission_id: str
    pilot_id: str
    aircraft_name: str
    kills: List[KillEvent] = field(default_factory=list)
    losses: List[LossEvent] = field(default_factory=list)
