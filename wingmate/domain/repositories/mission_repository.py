from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from wingmate.domain.entities.mission import Mission


class MissionRepository(ABC):
    @abstractmethod
    def list_missions(self, campaign_id: str) -> List[Mission]:
        raise NotImplementedError
