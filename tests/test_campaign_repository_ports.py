import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.campaign_query_service import CampaignQueryService
from app.core.repositories import Campaign, CampaignRepositoryPort, JsonCampaignRepository
from app.core.data_parser import IL2DataParser


class _FakeCampaignRepo(CampaignRepositoryPort):
    def __init__(self, campaign: Optional[Campaign] = None, missions: Optional[List[Dict[str, Any]]] = None):
        self._campaign = campaign
        self._missions = missions or []

    def get_campaign(self, name: str) -> Optional[Campaign]:
        return self._campaign

    def get_missions(self, campaign_name: str, serial: str) -> List[Dict[str, Any]]:
        return self._missions


def test_json_campaign_repository_reads_campaign_and_missions(tmp_path: Path):
    base = tmp_path / "pwcg"
    campaign_name = "camp"
    campaign_dir = base / "User" / "Campaigns" / campaign_name
    reports_dir = campaign_dir / "CombatReports" / "123"
    reports_dir.mkdir(parents=True, exist_ok=True)

    (campaign_dir / "Campaign.json").write_text(
        '{"referencePlayerSerialNumber":"123","referencePlayerSquadronName":"Jasta 1","campaignDate":"19180101"}',
        encoding="utf-8",
    )
    (reports_dir / "1.json").write_text('{"date":"19180101"}', encoding="utf-8")

    repo = JsonCampaignRepository(IL2DataParser(base))

    campaign = repo.get_campaign(campaign_name)
    assert campaign is not None
    assert campaign.player_serial == "123"
    assert campaign.squadron_name == "Jasta 1"

    missions = repo.get_missions(campaign_name, "123")
    assert isinstance(missions, list)
    assert len(missions) == 1


def test_campaign_query_service_uses_repository_port():
    campaign = Campaign(name="camp", player_serial="42", squadron_name="Esc 1")
    repo = _FakeCampaignRepo(campaign=campaign, missions=[{"id": 1}])
    service = CampaignQueryService(repo)

    loaded = service.get_campaign("camp")
    assert loaded is not None
    assert loaded.player_serial == "42"

    missions = service.get_campaign_missions("camp")
    assert missions == [{"id": 1}]


def test_campaign_query_service_returns_empty_when_campaign_missing():
    repo = _FakeCampaignRepo(campaign=None, missions=[{"id": 1}])
    service = CampaignQueryService(repo)

    assert service.get_campaign_missions("missing") == []
