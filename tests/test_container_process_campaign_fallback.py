from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.container import AppContainer


class _FakeProcessor:
    def __init__(self, result):
        self._result = result

    def process_campaign(self, _campaign_name: str):
        return self._result


class _FakeParser:
    def __init__(self, campaigns):
        self._campaigns = campaigns

    def get_campaigns(self):
        return self._campaigns


class _FakeCpRepo:
    def __init__(self, process_result=None, campaigns=None, raises=False):
        self._process_result = process_result
        self._campaigns = campaigns or []
        self._raises = raises

    def process_career(self, _campaign_name: str):
        if self._raises:
            raise RuntimeError("cp.db unavailable")
        return self._process_result

    def list_career_ids(self):
        if self._raises:
            raise RuntimeError("cp.db unavailable")
        return self._campaigns


def test_process_campaign_cp_db_success_path(tmp_path: Path, monkeypatch):
    cp_db = tmp_path / "cp.db"
    cp_db.write_text("x", encoding="utf-8")

    container = AppContainer(str(tmp_path))
    container.set_cp_db_path(cp_db)

    monkeypatch.setattr(container, "get_cp_db_repository", lambda: _FakeCpRepo(process_result={"source": "cp"}))

    assert container.process_campaign("any") == {"source": "cp"}


def test_process_campaign_cp_db_raises_falls_back_to_json(tmp_path: Path, monkeypatch):
    cp_db = tmp_path / "cp.db"
    cp_db.write_text("x", encoding="utf-8")

    container = AppContainer(str(tmp_path))
    container.set_cp_db_path(cp_db)

    monkeypatch.setattr(container, "get_cp_db_repository", lambda: _FakeCpRepo(raises=True))
    monkeypatch.setattr(container, "get_processor", lambda: _FakeProcessor({"source": "json"}))

    assert container.process_campaign("any") == {"source": "json"}


def test_process_campaign_without_cp_db_uses_json_directly(monkeypatch):
    container = AppContainer("")
    monkeypatch.setattr(container, "get_processor", lambda: _FakeProcessor({"source": "json"}))

    assert container.process_campaign("any") == {"source": "json"}


def test_source_pwcg_json_bypasses_cp_db_even_when_available(tmp_path: Path, monkeypatch):
    cp_db = tmp_path / "cp.db"
    cp_db.write_text("x", encoding="utf-8")

    container = AppContainer(str(tmp_path))
    container.set_cp_db_path(cp_db)
    container.set_source_mode(AppContainer.SOURCE_PWCG_JSON)

    monkeypatch.setattr(container, "get_cp_db_repository", lambda: (_ for _ in ()).throw(AssertionError("should not use cp.db")))
    monkeypatch.setattr(container, "get_processor", lambda: _FakeProcessor({"source": "json-only"}))

    assert container.process_campaign("any") == {"source": "json-only"}


def test_list_campaigns_cp_db_to_json_fallback_chain(tmp_path: Path, monkeypatch):
    cp_db = tmp_path / "cp.db"
    cp_db.write_text("x", encoding="utf-8")

    container = AppContainer(str(tmp_path))
    container.set_cp_db_path(cp_db)

    monkeypatch.setattr(container, "get_cp_db_repository", lambda: _FakeCpRepo(campaigns=["CP-1"]))
    assert container.list_campaigns() == ["CP-1"]

    monkeypatch.setattr(container, "get_cp_db_repository", lambda: _FakeCpRepo(raises=True))
    monkeypatch.setattr(container, "get_parser", lambda: _FakeParser(["JSON-1"]))
    assert container.list_campaigns() == ["JSON-1"]


def test_has_cp_db_truth_table(tmp_path: Path):
    container = AppContainer(str(tmp_path))

    container._cp_db_path = None
    assert container.has_cp_db() is False

    container._cp_db_path = tmp_path / "missing_cp.db"
    assert container.has_cp_db() is False

    valid = tmp_path / "cp.db"
    valid.write_text("ok", encoding="utf-8")
    container._cp_db_path = valid
    assert container.has_cp_db() is True
