from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from wingmate.domain.entities.squadron import Squadron


class SquadronRepository(ABC):
    @abstractmethod
    def get_squadron(self, squadron_id: str) -> Optional[Squadron]:
        raise NotImplementedError
