import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.core.squadron_enrichment_service import SquadronEnrichmentService


def test_extract_fields_with_airfields_dict():
    service = SquadronEnrichmentService()
    data = {
        "squadronName": "Jasta 11",
        "country": "GERMANY",
        "airfields": {
            "19180101": "Base A",
            "19180201": "Base B",
        },
    }

    name, country, airfields = service.extract_fields(data)

    assert name == "Jasta 11"
    assert country == "GERMANY"
    assert airfields == [
        {"start": "19180101", "end": "19180201", "airfield": "Base A"},
        {"start": "19180201", "end": "", "airfield": "Base B"},
    ]


def test_build_payload_uses_source_and_history(tmp_path: Path):
    service = SquadronEnrichmentService()
    src = tmp_path / "42.json"
    src.write_text('{"name":"Esc 42", "nation":"FRANCE", "airfields": []}', encoding="utf-8")

    base_data = service.read_json(src)
    payload = service.build_enriched_payload(
        base_data=base_data,
        source_path=src,
        history="  texto historico  ",
        emblem_rel="squadrons/images/42.png",
    )

    assert payload["squadronId"] == "42"
    assert payload["squadronName"] == "Esc 42"
    assert payload["country"] == "FRANCE"
    assert payload["history"] == "texto historico"
    assert payload["emblemImage"] == "squadrons/images/42.png"
    assert payload["source"]["pwcg_squadron_file"] == str(src)


def test_read_json_invalid_raises_value_error(tmp_path: Path):
    service = SquadronEnrichmentService()
    broken = tmp_path / "broken.json"
    broken.write_text("{invalid}", encoding="utf-8")

    with pytest.raises(ValueError):
        service.read_json(broken)


def test_read_json_schema_invalid_raises_value_error(tmp_path: Path):
    service = SquadronEnrichmentService()
    invalid_schema = tmp_path / "invalid_schema.json"
    invalid_schema.write_text('{"name":123, "airfields":"oops"}', encoding="utf-8")

    with pytest.raises(ValueError):
        service.read_json(invalid_schema)


def test_save_enriched_payload_rejects_invalid_schema(tmp_path: Path):
    service = SquadronEnrichmentService()
    out = tmp_path / "out.json"

    with pytest.raises(ValueError):
        service.save_enriched_payload(
            out,
            {
                "squadronId": "11",
                # squadronName ausente
                "country": "GERMANY",
                "history": "h",
                "emblemImage": "",
                "airfields": [],
                "source": {"pwcg_squadron_file": "x"},
            },
        )
