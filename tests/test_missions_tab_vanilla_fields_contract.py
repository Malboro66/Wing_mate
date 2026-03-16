from pathlib import Path


def test_missions_tab_renders_vanilla_fields_in_labels_and_details():
    src = Path("app/ui/missions_tab.py").read_text(encoding="utf-8")

    assert "if m.victories is not None:" in src
    assert "if m.score is not None:" in src
    assert "if m.status is not None:" in src
    assert "if data.flight_time_s is not None:" in src
    assert "if data.victories is not None:" in src
    assert "if data.score is not None:" in src
    assert "if data.status is not None:" in src
