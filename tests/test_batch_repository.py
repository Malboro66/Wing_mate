import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.batch_repository import JsonBatchRepository
from app.core.data_parser import IL2DataParser


def test_json_batch_repository_load_many_and_resolve_many(tmp_path: Path):
    base = tmp_path / "pwcg"
    d = base / "User" / "Campaigns" / "C1" / "Personnel"
    d.mkdir(parents=True)

    f1 = d / "a.json"
    f2 = d / "b.json"
    f1.write_text(json.dumps({"value": 1}), encoding="utf-8")
    f2.write_text(json.dumps({"value": 2}), encoding="utf-8")

    parser = IL2DataParser(base)
    repo = JsonBatchRepository(parser)

    loaded, stats = repo.load_many([f1, f2, d / "missing.json"])
    assert stats.requested == 3
    assert stats.loaded == 2

    resolved = repo.resolve_many(loaded, lambda _p, payload: payload.get("value") if isinstance(payload, dict) else None)
    assert sorted(resolved) == [1, 2]
