from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Dict

from app.core.data_parser import IL2DataParser


def benchmark_personnel_io_scenario(base_path: Path, campaign_name: str, runs: int = 3) -> Dict[str, float]:
    """Benchmark sintético de I/O para leitura de Personnel (naive vs batch)."""
    personnel_dir = base_path / "User" / "Campaigns" / campaign_name / "Personnel"
    files = sorted(personnel_dir.glob("*.json"))
    if not files:
        return {"files": 0.0, "naive_ms": 0.0, "batch_ms": 0.0, "gain_pct": 0.0}

    safe_runs = max(1, int(runs or 1))

    naive_start = perf_counter()
    for _ in range(safe_runs):
        for p in files:
            parser = IL2DataParser(base_path)
            parser.get_json_data(p)
    naive_ms = (perf_counter() - naive_start) * 1000.0

    batch_start = perf_counter()
    for _ in range(safe_runs):
        parser = IL2DataParser(base_path)
        parser.get_json_many(files)
    batch_ms = (perf_counter() - batch_start) * 1000.0

    gain_pct = 0.0
    if naive_ms > 0:
        gain_pct = ((naive_ms - batch_ms) / naive_ms) * 100.0

    return {
        "files": float(len(files)),
        "naive_ms": naive_ms,
        "batch_ms": batch_ms,
        "gain_pct": gain_pct,
    }
