import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.weather_parser import WeatherParser


def test_weather_parser_extracts_structured_fields_and_raw_block():
    description = """
Mission briefing line
Weather Report:
Visibility: 10 km
Clouds: Scattered at 2000m
Wind: 18 km/h NW
Temperature: 12 C

Objective: Escort bombers
"""

    report = WeatherParser.parse(description)

    assert report.visibility == "10 km"
    assert report.clouds == "Scattered at 2000m"
    assert report.wind_speed.startswith("18")
    assert report.wind_dir == "NW"
    assert report.temperature == "12 C"
    assert "Objective" not in report.raw


def test_weather_parser_returns_defaults_when_missing_section():
    report = WeatherParser.parse("No weather block here")

    assert report.raw == "Não disponível"
    assert report.visibility == "Não disponível"
