from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Protocol, Tuple


class SquadronEnrichmentDomainPort(Protocol):
    """Contrato da camada de domínio para enriquecimento de esquadrões."""

    def read_json(self, path: Path) -> Dict[str, Any]:
        ...

    def resolve_id_and_name(self, data: Dict[str, Any], path: Path) -> Tuple[str, str]:
        ...

    def extract_fields(self, data: Dict[str, Any]) -> Tuple[str, str, List[Dict[str, str]]]:
        ...

    def build_enriched_payload(
        self,
        base_data: Dict[str, Any],
        source_path: Path,
        history: str,
        emblem_rel: str,
    ) -> Dict[str, Any]:
        ...

    def save_enriched_payload(self, output_path: Path, payload: Dict[str, Any]) -> None:
        ...
