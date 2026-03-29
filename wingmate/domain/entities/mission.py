from dataclasses import dataclass, field
from typing import List

from wingmate.domain.entities.sortie import Sortie
from wingmate.domain.value_objects.mission_result import MissionResult


@dataclass
class Mission:
    mission_id: str
    date: str
    result: MissionResult = MissionResult.UNKNOWN
    sorties: List[Sortie] = field(default_factory=list)

    def success_rate(self) -> float:
        return 1.0 if self.result == MissionResult.SUCCESS else 0.0
