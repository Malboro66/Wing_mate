# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/core/squadron_enrichment_service.py
# Serviço de domínio para enriquecimento de metadados de esquadrões
# ===================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from utils.file_operations import atomic_json_write, safe_read_json


class SquadronEnrichmentService:
    """Encapsula regras de negócio de enriquecimento de esquadrões."""

    NAME_KEYS: Tuple[str, ...] = (
        "squadronName",
        "name",
        "displayName",
        "id",
        "squadron_id",
    )
    COUNTRY_KEYS: Tuple[str, ...] = ("country", "nation", "countryCode")

    def read_json(self, path: Path) -> Dict[str, Any]:
        """Lê JSON com API segura padronizada e fallback de encoding."""
        data = safe_read_json(path, default=None)
        if isinstance(data, dict):
            return data

        try:
            with path.open("r", encoding="latin-1") as f:
                parsed = json.load(f)
            if isinstance(parsed, dict):
                return parsed
        except (UnicodeDecodeError, json.JSONDecodeError, OSError):
            pass

        raise ValueError(f"JSON inválido ou ilegível: {path}")

    def resolve_id_and_name(self, data: Dict[str, Any], path: Path) -> Tuple[str, str]:
        """Resolve identificador e nome de esquadrão a partir do JSON base."""
        sq_id = path.stem
        for key in self.NAME_KEYS:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return sq_id, value.strip()
        return sq_id, sq_id

    def extract_fields(self, data: Dict[str, Any]) -> Tuple[str, str, List[Dict[str, str]]]:
        """Extrai nome, país e histórico de aeródromos normalizados."""
        name = self._first_string(data, self.NAME_KEYS)
        country = self._first_string(data, self.COUNTRY_KEYS)

        airfields: List[Dict[str, str]] = []

        def add_af(start: Any, end: Any, airfield: Any) -> None:
            start_text = str(start or "").strip()
            end_text = str(end or "").strip()
            airfield_text = str(airfield or "").strip()
            if airfield_text:
                airfields.append(
                    {"start": start_text, "end": end_text, "airfield": airfield_text}
                )

        af_dict = data.get("airfields")
        if isinstance(af_dict, dict):
            items = sorted(((str(k), str(v)) for k, v in af_dict.items()), key=lambda x: x[0])
            for index, (start, af_name) in enumerate(items):
                end = items[index + 1][0] if index + 1 < len(items) else ""
                add_af(start, end, af_name)

        if isinstance(data.get("airfields"), list):
            for item in data["airfields"]:
                if isinstance(item, dict):
                    add_af(
                        item.get("start"),
                        item.get("end"),
                        item.get("airfield") or item.get("base") or item.get("name"),
                    )

        if isinstance(data.get("airfieldHistory"), list):
            for item in data["airfieldHistory"]:
                if isinstance(item, dict):
                    add_af(item.get("from"), item.get("to"), item.get("airfield") or item.get("name"))

        if not airfields and isinstance(data.get("bases"), list):
            for item in data["bases"]:
                if isinstance(item, dict):
                    add_af(
                        item.get("startDate"),
                        item.get("endDate"),
                        item.get("airfield") or item.get("base"),
                    )

        return name, country, airfields

    def build_enriched_payload(
        self,
        base_data: Dict[str, Any],
        source_path: Path,
        history: str,
        emblem_rel: str,
    ) -> Dict[str, Any]:
        """Monta payload de metadados enriquecidos de esquadrão."""
        sq_id, sq_name = self.resolve_id_and_name(base_data, source_path)
        _name, country, airfields = self.extract_fields(base_data)

        return {
            "squadronId": sq_id,
            "squadronName": sq_name,
            "country": country or "",
            "history": history.strip(),
            "emblemImage": emblem_rel,
            "airfields": airfields,
            "source": {"pwcg_squadron_file": str(source_path)},
        }

    def save_enriched_payload(self, output_path: Path, payload: Dict[str, Any]) -> None:
        """Persiste payload em JSON UTF-8 com escrita atômica padronizada."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with atomic_json_write(output_path) as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _first_string(data: Dict[str, Any], keys: Tuple[str, ...]) -> str:
        for key in keys:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""
