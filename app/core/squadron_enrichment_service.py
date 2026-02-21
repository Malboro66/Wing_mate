# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/core/squadron_enrichment_service.py
# Serviço de domínio para enriquecimento de metadados de esquadrões
# ===================================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from utils.file_operations import atomic_json_write, safe_read_json


@dataclass(frozen=True)
class AirfieldEntry:
    start: str
    end: str
    airfield: str

    @classmethod
    def from_raw(cls, start: Any, end: Any, airfield: Any) -> "AirfieldEntry":
        start_text = str(start or "").strip()
        end_text = str(end or "").strip()
        airfield_text = str(airfield or "").strip()
        if not airfield_text:
            raise ValueError("Campo 'airfield' é obrigatório e não pode ser vazio")
        return cls(start=start_text, end=end_text, airfield=airfield_text)

    def to_dict(self) -> Dict[str, str]:
        return {"start": self.start, "end": self.end, "airfield": self.airfield}


@dataclass(frozen=True)
class EnrichedSquadronSchema:
    squadron_id: str
    squadron_name: str
    country: str
    history: str
    emblem_image: str
    airfields: List[AirfieldEntry]
    source_path: str

    def validate(self) -> None:
        if not self.squadron_id.strip():
            raise ValueError("Campo obrigatório inválido: squadronId")
        if not self.squadron_name.strip():
            raise ValueError("Campo obrigatório inválido: squadronName")
        if not isinstance(self.country, str):
            raise ValueError("Campo inválido: country")
        if not isinstance(self.history, str):
            raise ValueError("Campo inválido: history")
        if not isinstance(self.emblem_image, str):
            raise ValueError("Campo inválido: emblemImage")
        if not self.source_path.strip():
            raise ValueError("Campo obrigatório inválido: source.pwcg_squadron_file")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "squadronId": self.squadron_id,
            "squadronName": self.squadron_name,
            "country": self.country,
            "history": self.history,
            "emblemImage": self.emblem_image,
            "airfields": [a.to_dict() for a in self.airfields],
            "source": {"pwcg_squadron_file": self.source_path},
        }


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
            self._validate_input_schema(data)
            return data

        try:
            with path.open("r", encoding="latin-1") as f:
                parsed = json.load(f)
            if isinstance(parsed, dict):
                self._validate_input_schema(parsed)
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

        airfields: List[AirfieldEntry] = []

        def add_af(start: Any, end: Any, airfield: Any) -> None:
            try:
                airfields.append(AirfieldEntry.from_raw(start, end, airfield))
            except ValueError:
                return

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

        return name, country, [item.to_dict() for item in airfields]

    def build_enriched_payload(
        self,
        base_data: Dict[str, Any],
        source_path: Path,
        history: str,
        emblem_rel: str,
    ) -> Dict[str, Any]:
        """Monta payload de metadados enriquecidos de esquadrão validando schema."""
        sq_id, sq_name = self.resolve_id_and_name(base_data, source_path)
        _name, country, airfields_dicts = self.extract_fields(base_data)

        airfields = [
            AirfieldEntry.from_raw(a.get("start"), a.get("end"), a.get("airfield"))
            for a in airfields_dicts
        ]

        payload = EnrichedSquadronSchema(
            squadron_id=sq_id,
            squadron_name=sq_name,
            country=country or "",
            history=history.strip(),
            emblem_image=emblem_rel,
            airfields=airfields,
            source_path=str(source_path),
        )
        return payload.to_dict()

    def save_enriched_payload(self, output_path: Path, payload: Dict[str, Any]) -> None:
        """Persiste payload em JSON UTF-8 com escrita atômica padronizada."""
        self._validate_output_schema(payload)
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

    @staticmethod
    def _validate_input_schema(data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValueError("Schema inválido: JSON raiz deve ser um objeto")

        for key in ("squadronName", "name", "displayName", "id", "squadron_id"):
            value = data.get(key)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"Schema inválido: campo '{key}' deve ser string")

        airfields = data.get("airfields")
        if airfields is not None and not isinstance(airfields, (dict, list)):
            raise ValueError("Schema inválido: campo 'airfields' deve ser dict ou list")

    @staticmethod
    def _validate_output_schema(payload: Dict[str, Any]) -> None:
        required = ("squadronId", "squadronName", "country", "history", "emblemImage", "airfields", "source")
        for key in required:
            if key not in payload:
                raise ValueError(f"Schema de saída inválido: campo ausente '{key}'")

        if not isinstance(payload.get("airfields"), list):
            raise ValueError("Schema de saída inválido: 'airfields' deve ser lista")

        source = payload.get("source")
        if not isinstance(source, dict) or not isinstance(source.get("pwcg_squadron_file"), str):
            raise ValueError("Schema de saída inválido: source.pwcg_squadron_file inválido")
