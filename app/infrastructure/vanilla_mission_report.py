from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("IL2CampaignAnalyzer")


class VanillaMissionReportReader:
    """Reads IL-2 vanilla mission reports (.mlg) from FlightLogs."""

    _PRIMARY_PATTERN = "missionReport(*).mlg"

    def __init__(self, cp_db_path: Path) -> None:
        self._cp_db_path = Path(cp_db_path)

    def build_latest_report_summary(self, max_lines: int = 10) -> Optional[str]:
        report_path = self.latest_report_path()
        if report_path is None:
            return None

        try:
            blob = report_path.read_bytes()
        except OSError:
            logger.exception("flightlogs: failed to read mission report '%s'", report_path)
            return None

        chunks = self._extract_text_chunks(blob, max_lines=max_lines)
        header = f"Arquivo: {report_path.name}"
        if not chunks:
            return header

        body = "\n".join(f"- {chunk}" for chunk in chunks)
        return f"{header}\n{body}"

    def latest_report_path(self) -> Optional[Path]:
        logs_dir = self._resolve_flight_logs_dir()
        if logs_dir is None:
            return None

        candidates = [p for p in logs_dir.glob(self._PRIMARY_PATTERN) if p.is_file()]
        if not candidates:
            candidates = [p for p in logs_dir.glob("*.mlg") if p.is_file()]
        if not candidates:
            return None

        candidates.sort(key=self._safe_mtime, reverse=True)
        return candidates[0]

    def _resolve_flight_logs_dir(self) -> Optional[Path]:
        candidates: List[Path] = []
        for ancestor in [self._cp_db_path.parent, *self._cp_db_path.parents]:
            candidates.append(ancestor / "FlightLogs")
            candidates.append(ancestor / "data" / "FlightLogs")

        unique_candidates: List[Path] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = str(candidate).lower()
            if key in seen:
                continue
            seen.add(key)
            unique_candidates.append(candidate)

        for candidate in unique_candidates:
            try:
                if candidate.exists() and candidate.is_dir():
                    return candidate
            except OSError:
                continue
        return None

    @staticmethod
    def _safe_mtime(path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    @classmethod
    def _extract_text_chunks(cls, blob: bytes, max_lines: int = 10) -> List[str]:
        # missionReport is a binary file with embedded printable text blocks.
        raw_chunks = re.findall(rb"[ -~]{4,120}", blob)

        ordered: List[str] = []
        seen: set[str] = set()
        for raw in raw_chunks:
            text = raw.decode("ascii", errors="ignore").strip()
            if not text:
                continue
            if cls._is_noise(text):
                continue
            if text in seen:
                continue
            seen.add(text)
            ordered.append(text)

        if not ordered:
            return []

        keywords = (
            "mission",
            "pilot",
            "sopwith",
            "spad",
            "fokker",
            "albatros",
            "explosion",
            "flight",
            "botpilot",
        )

        prioritized = [text for text in ordered if any(k in text.lower() for k in keywords)]
        fallback = [text for text in ordered if text not in prioritized]
        merged = prioritized + fallback
        return merged[: max(1, int(max_lines))]

    @staticmethod
    def _is_noise(text: str) -> bool:
        if not re.search(r"[A-Za-z]", text):
            return True

        lowered = text.lower()
        if lowered.startswith("00000000-0000-0000-0000-"):
            return True
        if lowered.startswith("missions\\_gen.msnbin"):
            return True

        letters = sum(1 for ch in text if ch.isalpha())
        if letters < 2:
            return True

        if len(text) > 90 and " " not in text and "\\" not in text:
            return True

        return False

