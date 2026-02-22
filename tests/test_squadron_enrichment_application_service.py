import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.squadron_enrichment_application_service import (
    SquadronEnrichmentApplicationService,
)


class _FakeDomain:
    def __init__(self) -> None:
        self.saved: Tuple[Path, Dict[str, Any]] | None = None

    def read_json(self, path: Path) -> Dict[str, Any]:
        return {"name": "Esc 77", "country": "FRANCE", "airfields": []}

    def resolve_id_and_name(self, data: Dict[str, Any], path: Path) -> Tuple[str, str]:
        return path.stem, "Esc 77"

    def extract_fields(self, data: Dict[str, Any]) -> Tuple[str, str, List[Dict[str, str]]]:
        return "Esc 77", "FRANCE", [{"start": "", "end": "", "airfield": "A"}]

    def build_enriched_payload(
        self,
        base_data: Dict[str, Any],
        source_path: Path,
        history: str,
        emblem_rel: str,
    ) -> Dict[str, Any]:
        return {
            "squadronId": source_path.stem,
            "squadronName": "Esc 77",
            "country": "FRANCE",
            "history": history,
            "emblemImage": emblem_rel,
            "airfields": [],
            "source": {"pwcg_squadron_file": str(source_path)},
        }

    def save_enriched_payload(self, output_path: Path, payload: Dict[str, Any]) -> None:
        self.saved = (output_path, payload)


def test_load_preview_uses_domain_port(tmp_path: Path):
    app_service = SquadronEnrichmentApplicationService(_FakeDomain())
    country, airfields = app_service.load_preview(tmp_path / "77.json")

    assert country == "FRANCE"
    assert airfields == [{"start": "", "end": "", "airfield": "A"}]


def test_build_and_persist_payload(tmp_path: Path):
    domain = _FakeDomain()
    app_service = SquadronEnrichmentApplicationService(domain)

    source = tmp_path / "77.json"
    squadron_id, payload = app_service.build_payload(source, "hist", "img.png")

    assert squadron_id == "77"
    assert payload["history"] == "hist"
    assert payload["emblemImage"] == "img.png"

    out = tmp_path / "out.json"
    app_service.persist_payload(out, payload)

    assert domain.saved is not None
    assert domain.saved[0] == out
