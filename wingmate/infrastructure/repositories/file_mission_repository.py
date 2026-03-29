from wingmate.domain.entities.mission import Mission
from wingmate.domain.repositories.mission_repository import MissionRepository
from typing import List


class FileMissionRepository(MissionRepository):
    def list_missions(self, campaign_id: str) -> List[Mission]:
        del campaign_id
        return []
