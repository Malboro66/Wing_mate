import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_risk_matrix_document_covers_10_prioritized_flows_and_smoke_gate():
    doc = Path("docs/test_risk_matrix.md").read_text(encoding="utf-8")

    assert "## Top 10 fluxos priorizados para release" in doc
    for i in range(1, 11):
        assert f"{i}. " in doc

    assert "## Matriz risco × tipo de teste" in doc
    assert "## Smoke de release (rápido)" in doc
    assert "pytest -q" in doc


def test_quarantine_policy_has_sla_and_manifest():
    matrix = Path("docs/test_risk_matrix.md").read_text(encoding="utf-8")
    manifest = Path("tests/quarantine_manifest.md").read_text(encoding="utf-8")

    assert "Política de falha rápida" in matrix
    assert "SLA de correção" in matrix
    assert "@quarantine" in matrix

    assert "Quarantine manifest" in manifest
    assert "Estado atual" in manifest
