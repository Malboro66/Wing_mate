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
                "aircraft_badge": "Novato",
                "duty": "Escort",
                "locality": "Frontline",
                "airfield": "St. Omer",
                "weather": "Weather Report: Clear",
                "description": "Mission text",
                "flight_time_formatted": "1h 23m",
            }
        ]
    )

    assert missions == [
        Mission(
            date="01/01/1918",
            time="12:00",
            aircraft="SPAD",
            aircraft_badge="Novato",
            duty="Escort",
            locality="Frontline",
            airfield="St. Omer",
            weather="Weather Report: Clear",
            description="Mission text",
            flight_time_formatted="1h 23m",
        )
    ]


def test_validation_service_skips_non_dict_items():
    service = MissionValidationService()

    missions = service.validate([{"description": "ok"}, None, "bad"])

    assert len(missions) == 1
    assert missions[0].description == "ok"


def test_validation_service_propagates_locality_airfield_weather_defaults():
    service = MissionValidationService()

    missions = service.validate([{"description": "ok"}])

    assert len(missions) == 1
    assert missions[0].locality == ""
    assert missions[0].airfield == ""
    assert missions[0].weather == ""
