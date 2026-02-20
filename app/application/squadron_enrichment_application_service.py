from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from app.application.ports import SquadronEnrichmentDomainPort


class SquadronEnrichmentApplicationService:
    """Orquestra casos de uso entre UI e camada de domínio."""

    def __init__(self, domain_service: SquadronEnrichmentDomainPort) -> None:
        self._domain = domain_service

    def load_preview(self, source_path: Path) -> Tuple[str, List[Dict[str, str]]]:
        """Carrega dados necessários para exibição na UI (país + aeródromos)."""
        data = self._domain.read_json(source_path)
        _name, country, airfields = self._domain.extract_fields(data)
        return country, airfields

    def build_payload(self, source_path: Path, history: str, emblem_rel: str) -> Tuple[str, Dict[str, object]]:
        """Monta payload enriquecido e retorna também o identificador do esquadrão."""
        data = self._domain.read_json(source_path)
        squadron_id, _ = self._domain.resolve_id_and_name(data, source_path)
        payload = self._domain.build_enriched_payload(
            base_data=data,
            source_path=source_path,
            history=history,
            emblem_rel=emblem_rel,
        )
        return squadron_id, payload

    def persist_payload(self, output_path: Path, payload: Dict[str, object]) -> None:
        """Persiste payload validado via camada de domínio."""
        self._domain.save_enriched_payload(output_path, payload)
