from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class WeatherReport:
    visibility: str
    clouds: str
    wind_speed: str
    wind_dir: str
    temperature: str
    raw: str


class WeatherParser:
    _NA = "Não disponível"

    @classmethod
    def parse(cls, description: str) -> WeatherReport:
        text = str(description or "")
        block = cls._extract_weather_block(text)
        if not block:
            return WeatherReport(
                visibility=cls._NA,
                clouds=cls._NA,
                wind_speed=cls._NA,
                wind_dir=cls._NA,
                temperature=cls._NA,
                raw=cls._NA,
            )

        visibility = cls._extract_value(block, r"visibility\s*[:\-]\s*([^\n;]+)")
        clouds = cls._extract_value(block, r"clouds?\s*[:\-]\s*([^\n;]+)")
        temperature = cls._extract_value(block, r"temperature\s*[:\-]\s*([^\n;]+)")

        wind_speed = cls._extract_value(
            block,
            r"wind(?:\s+speed)?\s*[:\-]\s*([0-9]+(?:[\.,][0-9]+)?\s*(?:km/h|kph|m/s|mph|kt|knots?)?)",
        )
        wind_dir = cls._extract_value(
            block,
            r"wind(?:\s+(?:direction|dir))?\s*[:\-]\s*(?:[0-9]+(?:[\.,][0-9]+)?\s*(?:km/h|kph|m/s|mph|kt|knots?)\s*)?([a-z]{1,3}|north|south|east|west|northeast|northwest|southeast|southwest)",
        )

        raw = block.strip() or cls._NA
        return WeatherReport(
            visibility=visibility,
            clouds=clouds,
            wind_speed=wind_speed,
            wind_dir=wind_dir.upper() if wind_dir != cls._NA else wind_dir,
            temperature=temperature,
            raw=raw,
        )

    @classmethod
    def _extract_weather_block(cls, text: str) -> str:
        lines = text.splitlines()
        started = False
        collected: list[str] = []

        for line in lines:
            normalized = line.strip()
            lowered = normalized.lower()

            if not started and "weather report" in lowered:
                started = True
                collected.append(normalized)
                continue

            if not started:
                continue

            if not normalized and len(collected) >= 2:
                break

            if cls._looks_like_heading(normalized) and len(collected) >= 2:
                break

            collected.append(normalized)
            if len(collected) >= 12:
                break

        return "\n".join([line for line in collected if line]).strip()

    @staticmethod
    def _looks_like_heading(line: str) -> bool:
        if not line:
            return False
        heading_tokens = ("mission", "objective", "briefing", "debriefing", "intel", "targets")
        lowered = line.lower().strip(":")
        return any(lowered.startswith(token) for token in heading_tokens)

    @classmethod
    def _extract_value(cls, text: str, pattern: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return cls._NA
        return match.group(1).strip()
