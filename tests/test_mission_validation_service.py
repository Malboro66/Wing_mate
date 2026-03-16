import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.mission_validation_service import DataSource, Mission, MissionValidationService


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
                "source": "pwcg_json",
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
            source=DataSource.PWCG_JSON,
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


def test_validation_service_propagates_vanilla_fields():
    service = MissionValidationService()

    missions = service.validate([
        {
            "description": "ok",
            "victories": "2",
            "status": "1",
            "score": 345,
            "flight_time_s": "1200",
            "source": "vanilla_db",
        }
    ])

    assert len(missions) == 1
    assert missions[0].victories == 2
    assert missions[0].status == 1
    assert missions[0].score == 345
    assert missions[0].flight_time_s == 1200
    assert missions[0].source == DataSource.VANILLA_DB


def test_validation_service_defaults_to_unknown_source():
    service = MissionValidationService()

    missions = service.validate([{"description": "ok"}])

    assert missions[0].source == DataSource.UNKNOWN


def test_validation_service_accepts_datasource_enum_instance():
    service = MissionValidationService()

    missions = service.validate([{"source": DataSource.PWCG_JSON}])

    assert len(missions) == 1
    assert missions[0].source == DataSource.PWCG_JSON
