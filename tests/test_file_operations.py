import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import utils.file_operations as file_operations


def test_atomic_json_write_replaces_target_file(tmp_path: Path):
    target = tmp_path / "data.json"
    target.write_text('{"old": true}', encoding="utf-8")

    with file_operations.atomic_json_write(target) as f:
        json.dump({"new": True}, f)

    assert json.loads(target.read_text(encoding="utf-8")) == {"new": True}
    assert not list(tmp_path.glob('.tmp_*.json'))


def test_atomic_json_write_calls_fsync(tmp_path: Path, monkeypatch):
    target = tmp_path / "durable.json"
    called = []

    def fake_fsync(fd: int):
        called.append(fd)

    monkeypatch.setattr(file_operations.os, "fsync", fake_fsync)

    with file_operations.atomic_json_write(target) as f:
        json.dump({"durable": True}, f)

    assert called
    assert json.loads(target.read_text(encoding="utf-8")) == {"durable": True}
