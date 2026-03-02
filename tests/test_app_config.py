import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.app_config import AppConfig


class _FakeSettings:
    def __init__(self) -> None:
        self._data = {}

    def value(self, key: str, default=""):
        return self._data.get(key, default)

    def setValue(self, key: str, value) -> None:  # noqa: N802
        self._data[key] = value


def test_app_config_validates_and_gates_ww1(tmp_path: Path):
    settings = _FakeSettings()
    cfg = AppConfig(settings)

    il2 = tmp_path / "il2"
    rof = tmp_path / "rof"
    pwcg = tmp_path / "pwcg"
    il2.mkdir()
    rof.mkdir()
    pwcg.mkdir()

    cfg.set_path(AppConfig.KEY_IL2_FC, str(il2))
    cfg.set_path(AppConfig.KEY_ROF, str(rof))
    cfg.set_path(AppConfig.KEY_PWCG, str(pwcg))

    assert cfg.ww1_ready() is True
    assert cfg.ww2_ready() is False
