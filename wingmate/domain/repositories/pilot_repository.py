from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from wingmate.domain.entities.pilot import Pilot


class PilotRepository(ABC):
    @abstractmethod
    def get_pilot(self, pilot_id: str) -> Optional[Pilot]:
        raise NotImplementedError
