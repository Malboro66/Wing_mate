import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.io_benchmark import benchmark_personnel_io_scenario


def test_benchmark_personnel_io_scenario_reports_metrics(tmp_path: Path):
    base = tmp_path / "pwcg"
    personnel_dir = base / "User" / "Campaigns" / "CampBench" / "Personnel"
    personnel_dir.mkdir(parents=True)

    payload = {"squadronMemberCollection": {"p1": {"name": "Pilot", "country": "GER"}}}
    for idx in range(30):
        (personnel_dir / f"{idx}.json").write_text(json.dumps(payload), encoding="utf-8")

    metrics = benchmark_personnel_io_scenario(base, "CampBench", runs=2)

    assert metrics["files"] == 30.0
    assert metrics["naive_ms"] >= 0.0
    assert metrics["batch_ms"] >= 0.0
    assert -100.0 <= metrics["gain_pct"] <= 100.0
