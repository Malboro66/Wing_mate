import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.data_parser import IL2DataParser
from app.core.data_processor import IL2DataProcessor


def _build_campaign_tree(root: Path, campaign_name: str = "camp1") -> Path:
    campaign_dir = root / "User" / "Campaigns" / campaign_name
    campaign_dir.mkdir(parents=True, exist_ok=True)
    return campaign_dir


def test_parser_get_campaigns_sorted(tmp_path: Path):
    base = tmp_path / "pwcg"
    campaigns = base / "User" / "Campaigns"
    (campaigns / "Zulu").mkdir(parents=True)
    (campaigns / "Alpha").mkdir(parents=True)

    parser = IL2DataParser(base)
    assert parser.get_campaigns() == ["Alpha", "Zulu"]


def test_parser_get_campaign_aces_supports_multiple_formats(tmp_path: Path):
    base = tmp_path / "pwcg"
    campaign_dir = _build_campaign_tree(base)
    aces_path = campaign_dir / "CampaignAces.json"

    parser = IL2DataParser(base)

    # formato lista direta
    aces_path.write_text('[{"name":"Ace 1"}]', encoding="utf-8")
    assert parser.get_campaign_aces("camp1") == [{"name": "Ace 1"}]

    # formato dict com chave aces
    aces_path.write_text('{"aces":[{"name":"Ace 2"}]}', encoding="utf-8")
    parser._get_json_data_cached.cache_clear()
    assert parser.get_campaign_aces("camp1") == [{"name": "Ace 2"}]

    # formato dict com chave acesInCampaign
    aces_path.write_text('{"acesInCampaign":{"1":{"name":"Ace 3"}}}', encoding="utf-8")
    parser._get_json_data_cached.cache_clear()
    assert parser.get_campaign_aces("camp1") == [{"name": "Ace 3"}]


def test_parser_get_campaign_info_returns_empty_when_missing(tmp_path: Path):
    parser = IL2DataParser(tmp_path / "pwcg")
    assert parser.get_campaign_info("missing") == {}


def test_processor_format_date_and_status_mapping():
    processor = IL2DataProcessor(None)

    assert processor.format_date("19180101") == "01/01/1918"
    assert processor.format_date("invalid") == "invalid"
    assert processor.get_pilot_status(2) == "Morto em Combate (KIA)"
    assert processor.get_pilot_status(999) == "Desconhecido"


def test_processor_process_squadron_data_converts_and_sorts():
    processor = IL2DataProcessor(None)
    squadron_personnel = {
        "squadronMemberCollection": {
            "a": {
                "name": "Pilot A",
                "rank": "Lt",
                "victories": [1, 2, 3],
                "missionFlown": "12",
                "pilotActiveStatus": 1,
            },
            "b": {
                "name": "Pilot B",
                "rank": "Sgt",
                "victories": "2",
                "missionFlown": 4,
                "pilotActiveStatus": 4,
            },
        }
    }

    result = processor.process_squadron_data(squadron_personnel)

    assert result[0]["name"] == "Pilot A"
    assert result[0]["victories"] == 3
    assert result[0]["missions_flown"] == 12
    assert result[1]["status"] == "Capturado (POW)"


def test_processor_process_aces_data_counts_and_sorts():
    processor = IL2DataProcessor(None)
    aces_raw = [
        {"name": "Ace B", "victories": [1], "missionFlown": 2, "rank": "R2", "country": "C2"},
        {"name": "Ace A", "victories": [1, 2, 3], "missionFlown": 8, "rank": "R1", "country": "C1"},
    ]

    result = processor.process_aces_data(aces_raw)

    assert result[0]["name"] == "Ace A"
    assert result[0]["victories"] == 3
    assert result[1]["name"] == "Ace B"
