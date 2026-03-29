from dataclasses import dataclass, field
from typing import List

from wingmate.domain.entities.mission import Mission
from wingmate.domain.entities.squadron import Squadron


@dataclass
class Campaign:
    campaign_id: str
    name: str
    missions: List[Mission] = field(default_factory=list)
    squadrons: List[Squadron] = field(default_factory=list)
