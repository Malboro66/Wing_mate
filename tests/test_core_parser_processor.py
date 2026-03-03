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
    parser.clear_cache()
    assert parser.get_campaign_aces("camp1") == [{"name": "Ace 2"}]

    # formato dict com chave acesInCampaign
    aces_path.write_text('{"acesInCampaign":{"1":{"name":"Ace 3"}}}', encoding="utf-8")
    parser.clear_cache()
    assert parser.get_campaign_aces("camp1") == [{"name": "Ace 3"}]


def test_parser_get_campaign_info_returns_empty_when_missing(tmp_path: Path):
    parser = IL2DataParser(tmp_path / "pwcg")
    assert parser.get_campaign_info("missing") == {}




def test_parser_clear_cache_refreshes_changed_file(tmp_path: Path):
    base = tmp_path / "pwcg"
    campaign_dir = _build_campaign_tree(base)
    campaign_file = campaign_dir / "Campaign.json"

    parser = IL2DataParser(base)

    campaign_file.write_text('{"name":"v1"}', encoding="utf-8")
    assert parser.get_campaign_info("camp1") == {"name": "v1"}

    campaign_file.write_text('{"name":"v2"}', encoding="utf-8")
    assert parser.get_campaign_info("camp1") == {"name": "v1"}

    parser.clear_cache()
    assert parser.get_campaign_info("camp1") == {"name": "v2"}


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


def test_parser_exposes_cache_metrics_for_observability(tmp_path: Path):
    base = tmp_path / "pwcg"
    campaign_dir = _build_campaign_tree(base)
    campaign_file = campaign_dir / "Campaign.json"
    campaign_file.write_text('{"name":"v1"}', encoding="utf-8")

    parser = IL2DataParser(base)

    parser.get_campaign_info("camp1")
    parser.get_campaign_info("camp1")

    metrics = parser.get_cache_metrics()
    assert metrics["misses"] >= 1
    assert metrics["hits"] >= 1
    assert metrics["entries"] >= 1


def test_parser_clear_cache_resets_metrics(tmp_path: Path):
    base = tmp_path / "pwcg"
    campaign_dir = _build_campaign_tree(base)
    (campaign_dir / "Campaign.json").write_text('{"name":"v1"}', encoding="utf-8")

    parser = IL2DataParser(base)
    parser.get_campaign_info("camp1")
    assert parser.get_cache_metrics()["entries"] >= 1

    parser.clear_cache()
    metrics = parser.get_cache_metrics()
    assert metrics == {"hits": 0, "misses": 0, "entries": 0}


def test_processor_process_pilot_data_calculates_xp_formula():
    processor = IL2DataProcessor(None)

    campaign_info = {"referencePlayerName": "Pilot A", "referencePlayerSquadronName": "Esc 1"}
    reports = [
        {"confirmedVictory": 2, "pilotStatus": "active"},
        {"confirmedVictory": 1, "pilotStatus": "KIA"},
        {"confirmedVictory": 0, "pilotStatus": "landed"},
    ]

    pilot = processor.process_pilot_data(campaign_info, reports)

    # XP = (Missões*100) + (Vitórias*500) + (Sobrevivência*200)
    # Missões=3, Vitórias=3, Sobrevivência=2
    assert pilot["xp"] == (3 * 100) + (3 * 500) + (2 * 200)
    assert pilot["total_victories"] == 3
    assert pilot["survival_count"] == 2


def test_processor_process_pilot_data_applies_morale_effects():
    processor = IL2DataProcessor(None)
    campaign_info = {"referencePlayerName": "Pilot B", "referencePlayerSquadronName": "Esc 2"}

    reports_high = [
        {"result": "vitoria", "confirmedVictory": 1},
        {"result": "victory", "confirmedVictory": 1},
        {"result": "vitoria", "confirmedVictory": 1},
        {"result": "victory", "confirmedVictory": 1},
        {"result": "vitoria", "confirmedVictory": 1},
    ]
    pilot_high = processor.process_pilot_data(campaign_info, reports_high)
    assert pilot_high["morale"] > 80
    assert pilot_high["xp_multiplier"] > 1.0
    assert pilot_high["needs_rest"] is False

    reports_low = [
        {"result": "perda_ala", "confirmedVictory": 0},
        {"result": "wingman lost", "confirmedVictory": 0},
        {"result": "perda_ala", "confirmedVictory": 0},
        {"result": "wingman killed", "confirmedVictory": 0},
        {"result": "perda_ala", "confirmedVictory": 0},
    ]
    pilot_low = processor.process_pilot_data(campaign_info, reports_low)
    assert pilot_low["morale"] < 20
    assert pilot_low["morale_state"] == "Exausto"
    assert pilot_low["needs_rest"] is True


def test_parser_clean_pilot_name_removes_rank_and_normalizes_spaces():
    parser = IL2DataParser(Path.cwd())
    cleaned = parser._clean_pilot_name("Lt.   Hans    Schmidt")
    assert cleaned == "Hans Schmidt"


def test_parser_clean_pilot_name_removes_lt_and_capt_variants():
    parser = IL2DataParser(Path.cwd())

    assert parser._clean_pilot_name("Lt. Otto Frank") == "Otto Frank"
    assert parser._clean_pilot_name("Capt René Fonck") == "René Fonck"
    assert parser._clean_pilot_name("capt  Alice  Dupont") == "Alice Dupont"


def test_parser_find_mission_file_matches_uses_date_regex_fallback(tmp_path: Path):
    parser = IL2DataParser(tmp_path)
    candidates = [
        tmp_path / "mission_1918-01-03_alpha.json",
        tmp_path / "other_1918-01-02.json",
    ]

    matches = parser._find_mission_file_matches(candidates, "", "1918-01-03")

    assert matches
    assert matches[0].name == "mission_1918-01-03_alpha.json"


def test_parser_find_mission_file_matches_regex_rejects_non_yyyy_mm_dd_dates(tmp_path: Path):
    parser = IL2DataParser(tmp_path)
    candidates = [
        tmp_path / "mission_1918_01_03_alpha.json",
        tmp_path / "mission_03-01-1918_beta.json",
    ]

    matches = parser._find_mission_file_matches(candidates, "", "1918-01-03")

    assert matches == []


def test_parser_get_json_many_uses_resolved_path_for_fallback():
    src = Path("app/core/data_parser.py").read_text(encoding="utf-8")
    assert "resolved_path: Path = file_path" in src
    assert "self._load_json_file(resolved_path)" in src


def test_process_missions_data_includes_pilots_in_mission_field():
    processor = IL2DataProcessor(None)

    class _Parser:
        def get_mission_data(self, _campaign, _report):
            return {}

    processor.parser = _Parser()
    reports = [{"date": "19180101", "haReport": "Pilot A\nPilot B", "type": "SPAD"}]
    missions, _ = processor.process_missions_data("camp", reports, "1")

    assert "pilots_in_mission" in missions[0]
    assert missions[0]["pilots_in_mission"] == ["Pilot A", "Pilot B"]


def test_process_campaign_preserves_pilots_in_mission_in_final_payload():
    processor = IL2DataProcessor(None)

    class _Parser:
        def get_campaign_info(self, _campaign):
            return {
                "referencePlayerSerialNumber": "1",
                "referencePlayerName": "Pilot A",
                "referencePlayerSquadronName": "Esc 1",
            }

        def get_combat_reports(self, _campaign, _serial):
            return [{"date": "19180101", "haReport": "Pilot A\nPilot B", "type": "SPAD"}]

        def get_mission_data(self, _campaign, _report):
            return {"missionHeader": {"airfield": "Field"}}

        def get_campaign_aces(self, _campaign):
            return []

        def get_squadron_personnel(self, _campaign, _squadron_id):
            return {}

    processor.parser = _Parser()
    payload = processor.process_campaign("camp")

    assert payload["missions"][0]["pilots_in_mission"] == ["Pilot A", "Pilot B"]


def test_resolve_aircraft_badge_prioritizes_ace_by_confirmed_victories():
    processor = IL2DataProcessor(None)
    assert processor._resolve_aircraft_badge(7, 5) == "Ás do Modelo"


def test_process_pilot_data_does_not_use_setdefault_fallback_block():
    src = Path("app/core/data_processor.py").read_text(encoding="utf-8")
    assert "pilot.setdefault" not in src
