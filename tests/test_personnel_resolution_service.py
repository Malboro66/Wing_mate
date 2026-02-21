import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.personnel_resolution_service import PersonnelResolutionService
from app.core.data_parser import IL2DataParser


def test_personnel_resolution_returns_defaults_when_missing(tmp_path: Path):
    parser = IL2DataParser(tmp_path / "pwcg")
    service = PersonnelResolutionService(lambda: parser)

    result = service.resolve("campaign", "pilot")

    assert result.country_code == "GERMANY"
    assert result.display_name == "Germany"
    assert result.earned_medal_ids == frozenset()


def test_personnel_resolution_resolves_country_and_medals(tmp_path: Path):
    base = tmp_path / "pwcg"
    personnel_dir = base / "User" / "Campaigns" / "Camp1" / "Personnel"
    personnel_dir.mkdir(parents=True)

    payload = {
        "squadronMemberCollection": {
            "p1": {
                "name": "Ace Pilot",
                "country": "fr",
                "medals": [
                    {"medalImage": "croix.png"},
                    {"medalName": "Legion Honor"},
                ],
            }
        }
    }
    (personnel_dir / "member.json").write_text(json.dumps(payload), encoding="utf-8")

    parser = IL2DataParser(base)
    service = PersonnelResolutionService(lambda: parser)

    result = service.resolve("Camp1", "Ace Pilot")

    assert result.country_code == "FRANCE"
    assert result.display_name == "France"
    assert result.earned_medal_ids == frozenset({"croix", "legion_honor"})
