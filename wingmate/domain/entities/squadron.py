from dataclasses import dataclass, field
from typing import List

from wingmate.domain.entities.pilot import Pilot


@dataclass
class Squadron:
    squadron_id: str
    name: str
    country: str
    members: List[Pilot] = field(default_factory=list)

    def active_members(self) -> List[Pilot]:
        return [m for m in self.members if m.status.lower() == "active"]
