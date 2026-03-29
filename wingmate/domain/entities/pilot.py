from dataclasses import dataclass, field

from wingmate.domain.value_objects.pilot_rank import PilotRank


@dataclass
class Pilot:
    pilot_id: str
    name: str
    rank: PilotRank
    victories: int = 0
    missions_flown: int = 0
    status: str = "active"
    metadata: dict = field(default_factory=dict)

    def record_victory(self, amount: int = 1) -> None:
        self.victories = max(0, self.victories + max(0, amount))

    @property
    def kill_ratio(self) -> float:
        if self.missions_flown <= 0:
            return 0.0
        return self.victories / float(self.missions_flown)
