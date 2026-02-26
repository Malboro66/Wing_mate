# -*- coding: utf-8 -*-
"""Padrões mínimos de observabilidade estruturada para eventos de domínio."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from utils.structured_logger import StructuredLogger

# SLOs de UX (máquina de referência)
STARTUP_SLO_MS = 2500.0
TAB_SWITCH_SLO_MS = 200.0
CRITICAL_ACTION_SLO_MS = 500.0


class Events:
    SYNC_STARTED = "sync_started"
    SYNC_SUCCEEDED = "sync_succeeded"
    SYNC_FAILED = "sync_failed"
    PROFILE_SAVED = "profile_saved"
    STARTUP_COMPLETED = "startup_completed"
    ACTION_MEASURED = "action_measured"
    OBSERVABILITY_REPORT_PUBLISHED = "observability_report_published"


class _MetricsState:
    def __init__(self) -> None:
        self.startup_time_ms: float = 0.0
        self.actions_total: int = 0
        self.actions_failed: int = 0
        self.action_duration_ms_total: float = 0.0
        self.max_tab_switch_ms: float = 0.0
        self.cache_hits: int = 0
        self.cache_misses: int = 0

    def snapshot(self) -> dict[str, float]:
        error_rate = (self.actions_failed / self.actions_total) if self.actions_total else 0.0
        cache_total = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / cache_total) if cache_total else 0.0
        avg_action = (self.action_duration_ms_total / self.actions_total) if self.actions_total else 0.0
        return {
            "startup_time_ms": round(self.startup_time_ms, 2),
            "action_duration_ms": round(avg_action, 2),
            "error_rate": round(error_rate, 4),
            "cache_hit_rate": round(cache_hit_rate, 4),
            "max_tab_switch_ms": round(self.max_tab_switch_ms, 2),
            "actions_total": float(self.actions_total),
            "actions_failed": float(self.actions_failed),
            "cache_hits": float(self.cache_hits),
            "cache_misses": float(self.cache_misses),
        }


_SESSION_ID = uuid.uuid4().hex
_METRICS = _MetricsState()


def get_session_id() -> str:
    return _SESSION_ID


def emit_event(logger: StructuredLogger, event: str, level: str = "info", **context: Any) -> None:
    logger.log(level, event, event=event, session_id=get_session_id(), **context)


def record_startup_time(logger: StructuredLogger, startup_time_ms: float) -> None:
    _METRICS.startup_time_ms = max(0.0, float(startup_time_ms))
    emit_event(logger, Events.STARTUP_COMPLETED, startup_time_ms=round(_METRICS.startup_time_ms, 2))


def record_action_duration(
    logger: StructuredLogger,
    action_name: str,
    duration_ms: float,
    success: bool,
) -> None:
    duration = max(0.0, float(duration_ms))
    _METRICS.actions_total += 1
    _METRICS.action_duration_ms_total += duration
    if action_name.startswith("tab_switch"):
        _METRICS.max_tab_switch_ms = max(_METRICS.max_tab_switch_ms, duration)
    if not success:
        _METRICS.actions_failed += 1

    emit_event(
        logger,
        Events.ACTION_MEASURED,
        action_name=action_name,
        action_duration_ms=round(duration, 2),
        success=bool(success),
    )


def record_cache_stats(cache_hits: int, cache_misses: int) -> None:
    _METRICS.cache_hits = max(0, int(cache_hits))
    _METRICS.cache_misses = max(0, int(cache_misses))


def metrics_snapshot() -> dict[str, float]:
    return _METRICS.snapshot()


def evaluate_ux_budget(snapshot: Optional[dict[str, float]] = None) -> dict[str, bool]:
    snap = snapshot or metrics_snapshot()
    return {
        "startup_within_slo": float(snap.get("startup_time_ms", 0.0)) <= STARTUP_SLO_MS,
        "tab_switch_within_slo": float(snap.get("max_tab_switch_ms", 0.0)) <= TAB_SWITCH_SLO_MS,
        "critical_action_within_slo": float(snap.get("action_duration_ms", 0.0)) <= CRITICAL_ACTION_SLO_MS,
    }


def publish_release_report(
    logger: StructuredLogger,
    release_tag: str,
    output_dir: Path,
    baseline_path: Optional[Path] = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot = metrics_snapshot()
    budget = evaluate_ux_budget(snapshot)

    baseline: dict[str, Any] = {}
    if baseline_path and baseline_path.exists():
        try:
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            baseline = {}

    delta = {}
    baseline_metrics = baseline.get("metrics", {}) if isinstance(baseline, dict) else {}
    for key in ("startup_time_ms", "action_duration_ms", "error_rate", "cache_hit_rate", "max_tab_switch_ms"):
        old = float(baseline_metrics.get(key, 0.0) or 0.0)
        delta[key] = round(float(snapshot.get(key, 0.0)) - old, 4)

    report = {
        "release": release_tag,
        "session_id": get_session_id(),
        "generated_at_epoch_ms": int(time.time() * 1000),
        "metrics": snapshot,
        "ux_budget": budget,
        "baseline_delta": delta,
    }

    report_path = output_dir / f"observability_{release_tag}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    emit_event(
        logger,
        Events.OBSERVABILITY_REPORT_PUBLISHED,
        release=release_tag,
        report_path=str(report_path),
        ux_budget=budget,
    )
    return report_path
