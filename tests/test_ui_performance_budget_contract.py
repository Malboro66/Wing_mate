import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_main_window_instruments_tab_switch_and_lazy_medals_reload():
    src = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    assert "self._medals_loaded_once" in src
    assert "self._medals_dirty" in src
    assert "record_action_duration(structured_logger, f\"tab_switch:" in src
    assert "set_context(country_code, display_name, earned_ids)" in src


def test_observability_exposes_ui_budget_thresholds():
    src = Path("utils/observability.py").read_text(encoding="utf-8")
    assert "STARTUP_SLO_MS = 2500.0" in src
    assert "TAB_SWITCH_SLO_MS = 200.0" in src
    assert "CRITICAL_ACTION_SLO_MS = 500.0" in src
    assert "def evaluate_ux_budget" in src
