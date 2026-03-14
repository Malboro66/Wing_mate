# -*- coding: utf-8 -*-
"""
Wing Mate - app/infrastructure/vanilla_squadron_catalog.py

Lê catálogo de esquadrões do IL-2 vanilla a partir de `Scg.gtp`.
"""

from __future__ import annotations

import logging
import mmap
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("IL2CampaignAnalyzer")

_ENTRY_MARKERS = (
    b"squadrons-codes.cfg\x00FILE\x01\x00\x00\x00",
    b"squadrons.cfg\x00FILE\x01\x00\x00\x00",
)

_SQUADRON_RE = re.compile(r"^\[Squadron=(\d+)\]$")
_NAME_RE = re.compile(r'^name="([^"]+)"')


@dataclass(frozen=True)
class _GtpEntry:
    path: str
    offset: int
    size: int


class VanillaSquadronCatalog:
    """Resolve nome de esquadrão pelo `configId` usando `Scg.gtp`."""

    def __init__(self, cp_db_path: Path) -> None:
        self._cp_db_path = cp_db_path
        self._scg_gtp_path = self._resolve_scg_gtp_path(cp_db_path)
        self._name_by_config_id: Dict[int, str] = {}
        self._loaded = False

    def get_name(self, config_id: int) -> Optional[str]:
        try:
            squad_id = int(config_id)
        except (TypeError, ValueError):
            return None

        if squad_id <= 0:
            return None

        self._ensure_loaded()
        return self._name_by_config_id.get(squad_id)

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        if not self._scg_gtp_path:
            logger.info("Scg.gtp não encontrado para resolver nomes de esquadrão vanilla.")
            return

        try:
            self._load_from_gtp(self._scg_gtp_path)
            logger.info(
                "Catálogo de esquadrões vanilla carregado: %s entradas (%s)",
                len(self._name_by_config_id),
                self._scg_gtp_path,
            )
        except Exception:
            logger.exception("Falha ao carregar catálogo de esquadrões de Scg.gtp")

    def _load_from_gtp(self, gtp_path: Path) -> None:
        with gtp_path.open("rb") as fh:
            with mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                entries = self._collect_squadron_entries(mm)
                for entry in entries:
                    text = self._read_entry_text(mm, entry)
                    if not text:
                        continue
                    for sq_id, sq_name in self._parse_squadron_names(text).items():
                        self._name_by_config_id.setdefault(sq_id, sq_name)

    def _collect_squadron_entries(self, mm: mmap.mmap) -> list[_GtpEntry]:
        entries: Dict[str, _GtpEntry] = {}
        for marker in _ENTRY_MARKERS:
            pos = 0
            while True:
                idx = mm.find(marker, pos)
                if idx < 0:
                    break
                pos = idx + 1

                path_start = mm.rfind(b"/scg/", max(0, idx - 128), idx + 1)
                if path_start < 0:
                    continue

                entry = self._read_entry_meta(mm, path_start)
                if not entry:
                    continue

                if not (
                    entry.path.endswith("/squadrons.cfg")
                    or entry.path.endswith("/squadrons-codes.cfg")
                ):
                    continue

                entries.setdefault(entry.path, entry)

        return list(entries.values())

    @staticmethod
    def _read_entry_meta(mm: mmap.mmap, path_start: int) -> Optional[_GtpEntry]:
        if path_start < 8:
            return None

        path_len = int.from_bytes(mm[path_start - 8 : path_start - 4], "little")
        if path_len <= 1 or path_len > 512:
            return None

        path_end = path_start + path_len - 1
        if path_end + 25 > len(mm):
            return None

        if mm[path_end] != 0:
            return None
        if mm[path_end + 1 : path_end + 5] != b"FILE":
            return None

        version = int.from_bytes(mm[path_end + 5 : path_end + 9], "little")
        if version != 1:
            return None

        offset = int.from_bytes(mm[path_end + 9 : path_end + 13], "little")
        size = int.from_bytes(mm[path_end + 13 : path_end + 17], "little")
        if offset <= 0 or size <= 0 or (offset + size) > len(mm):
            return None

        path_bytes = bytes(mm[path_start:path_end])
        try:
            path = path_bytes.decode("utf-8", errors="replace")
        except Exception:
            return None

        return _GtpEntry(path=path, offset=offset, size=size)

    @staticmethod
    def _read_entry_text(mm: mmap.mmap, entry: _GtpEntry) -> str:
        raw = bytes(mm[entry.offset : entry.offset + entry.size])
        if raw.startswith(b"STRMFILE") and len(raw) >= 32:
            raw = raw[32:]
        return raw.decode("utf-8", errors="replace")

    @staticmethod
    def _parse_squadron_names(text: str) -> Dict[int, str]:
        names: Dict[int, str] = {}
        current_id: Optional[int] = None

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            squad_match = _SQUADRON_RE.match(line)
            if squad_match:
                try:
                    current_id = int(squad_match.group(1))
                except (TypeError, ValueError):
                    current_id = None
                continue

            if current_id is None:
                continue

            name_match = _NAME_RE.match(line)
            if not name_match:
                continue

            name = str(name_match.group(1) or "").strip()
            if name:
                names.setdefault(current_id, name)

        return names

    @staticmethod
    def _resolve_scg_gtp_path(cp_db_path: Path) -> Optional[Path]:
        for ancestor in [cp_db_path.parent, *cp_db_path.parents]:
            candidate = ancestor / "Scg.gtp"
            if candidate.is_file():
                return candidate
            candidate = ancestor / "data" / "Scg.gtp"
            if candidate.is_file():
                return candidate
        return None
