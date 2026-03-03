import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.data_processor import IL2DataProcessor


class _FakeParser:
    def get_mission_data(self, _campaign, _report):
        return {}


def test_process_missions_data_assigns_progression_badges_and_aggregate_map():
    processor = IL2DataProcessor(None)
    processor.parser = _FakeParser()

    reports = []
    for i in range(21):
        reports.append(
            {
                "date": f"191801{(i % 9) + 1:02d}",
                "type": "SPAD XIII",
                "duty": "Escort",
                "confirmedVictory": 1 if i < 5 else 0,
            }
        )

    missions, _ = processor.process_missions_data("camp", reports, "42")

    assert missions[0]["aircraft_badge"] == "Novato"
    assert any(m["aircraft_badge"] == "Ás do Modelo" for m in missions)
    assert all(m["aircraft_badge"] != "Veterano" for m in missions)

    agg = processor._last_aircraft_progression.get("SPAD XIII", {})
    assert agg.get("missions") == 21
    assert agg.get("confirmed_victories") == 5
    assert agg.get("badge") == "Ás do Modelo"
