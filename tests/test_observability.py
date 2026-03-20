import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import observability
from utils.observability import (
    CRITICAL_ACTION_SLO_MS,
    Events,
    STARTUP_SLO_MS,
    TAB_SWITCH_SLO_MS,
    emit_event,
    evaluate_ux_budget,
    get_session_id,
    increment_cache_hit,
    increment_cache_miss,
    metrics_snapshot,
    publish_release_report,
    record_action_duration,
    record_cache_stats,
    record_startup_error,
    record_startup_phase,
    record_startup_time,
)


class _FakeStructuredLogger:
    def __init__(self) -> None:
        self.calls = []

    def log(self, level: str, message: str, **context):
        self.calls.append((level, message, context))


def test_emit_event_includes_standard_event_key_and_session_id():
    logger = _FakeStructuredLogger()

    emit_event(logger, Events.SYNC_STARTED, campaign_name="camp")

    assert len(logger.calls) == 1
    level, message, context = logger.calls[0]
    assert level == "info"
    assert message == Events.SYNC_STARTED
    assert context["event"] == Events.SYNC_STARTED
    assert context["campaign_name"] == "camp"
    assert context["session_id"] == get_session_id()


def test_metrics_snapshot_includes_required_catalog_and_budget_eval(monkeypatch):
    logger = _FakeStructuredLogger()
    record_startup_time(logger, STARTUP_SLO_MS - 10)
    record_startup_phase("imports", 15.0)
    record_startup_error("")
    record_action_duration(logger, "tab_switch:Medalhas", TAB_SWITCH_SLO_MS - 1, success=True)
    record_action_duration(logger, "sync_campaign", CRITICAL_ACTION_SLO_MS - 10, success=True)
    record_cache_stats(8, 2)
    monkeypatch.setattr(
        observability.cache_manager,
        "stats_para_observabilidade",
        lambda: {"cache_hits": 8.0, "cache_misses": 2.0, "cache_hit_rate": 0.8},
    )

    snapshot = metrics_snapshot()

    assert "startup_time_ms" in snapshot
    assert "startup_phases_ms" in snapshot
    assert "startup_error" in snapshot
    assert "action_duration_ms" in snapshot
    assert "error_rate" in snapshot
    assert "cache_hit_rate" in snapshot
    assert "max_tab_switch_ms" in snapshot

    budget = evaluate_ux_budget(snapshot)
    assert budget["startup_within_slo"] is True
    assert budget["tab_switch_within_slo"] is True
    assert budget["critical_action_within_slo"] is True


def test_publish_release_report_compares_with_baseline_and_budget(tmp_path: Path, monkeypatch):
    logger = _FakeStructuredLogger()

    baseline = {
        "metrics": {
            "startup_time_ms": 200.0,
            "action_duration_ms": 100.0,
            "error_rate": 0.5,
            "cache_hit_rate": 0.2,
            "max_tab_switch_ms": 300.0,
        }
    }
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    record_startup_time(logger, 120.0)
    record_startup_phase("main_window", 90.0)
    record_startup_error("RuntimeError: boom")
    record_action_duration(logger, "tab_switch:Perfil do Piloto", 90.0, success=True)
    record_action_duration(logger, "profile_save", 40.0, success=True)
    record_cache_stats(9, 1)
    monkeypatch.setattr(
        observability.cache_manager,
        "stats_para_observabilidade",
        lambda: {"cache_hits": 9.0, "cache_misses": 1.0, "cache_hit_rate": 0.9},
    )

    report_path = publish_release_report(
        logger,
        release_tag="r1",
        output_dir=tmp_path,
        baseline_path=baseline_path,
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["release"] == "r1"
    assert report["session_id"] == get_session_id()
    assert "baseline_delta" in report
    assert "startup_time_ms" in report["baseline_delta"]
    assert "ux_budget" in report
    assert report["metrics"]["startup_phases_ms"]["main_window"] == 90.0
    assert report["metrics"]["startup_error"] == "RuntimeError: boom"


def test_increment_cache_counters_updates_hit_rate(monkeypatch) -> None:
    record_cache_stats(0, 0)
    increment_cache_hit()
    increment_cache_miss()
    increment_cache_hit()
    monkeypatch.setattr(
        observability.cache_manager,
        "stats_para_observabilidade",
        lambda: {"cache_hits": 2.0, "cache_misses": 1.0, "cache_hit_rate": 0.6667},
    )

    snapshot = metrics_snapshot()
    assert snapshot["cache_hits"] >= 2
    assert snapshot["cache_misses"] >= 1
    assert snapshot["cache_hit_rate"] > 0
