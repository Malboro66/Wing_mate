from pathlib import Path

from utils import app_paths


def test_get_app_data_dir_uses_xdg_data_home_on_linux(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(app_paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))

    path = app_paths.get_app_data_dir()

    assert path == (tmp_path / "xdg-data" / app_paths.APP_DIR_NAME)
    assert path.is_dir()


def test_get_logs_and_observability_dirs_are_nested(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(app_paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))

    logs_dir = app_paths.get_logs_dir()
    observability_dir = app_paths.get_observability_dir()

    assert logs_dir.name == "logs"
    assert observability_dir == logs_dir / "observability"
    assert observability_dir.is_dir()
