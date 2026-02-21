import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.mission_validation_service import Mission, MissionValidationService


def test_validation_service_returns_typed_missions_once():
    service = MissionValidationService()

    missions = service.validate(
        [
            {
                "date": "01/01/1918",
                "time": "12:00",
                "aircraft": "SPAD",
                "duty": "Escort",
                "description": "Mission text",
            }
        ]
    )

    assert missions == [
        Mission(
            date="01/01/1918",
            time="12:00",
            aircraft="SPAD",
            duty="Escort",
            description="Mission text",
        )
    ]


def test_validation_service_skips_non_dict_items():
    service = MissionValidationService()

    missions = service.validate([{"description": "ok"}, None, "bad"])

    assert len(missions) == 1
    assert missions[0].description == "ok"
