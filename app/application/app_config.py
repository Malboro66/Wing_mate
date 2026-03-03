from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict



@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    reason: str = ""


class AppConfig:
    """Gerencia caminhos de simuladores e validações por era."""

    KEY_IL2_FC = "paths/il2_fc"
    KEY_ROF = "paths/rof"
    KEY_PWCG = "paths/pwcg"

    REQUIRED_WW1 = (KEY_IL2_FC, KEY_ROF, KEY_PWCG)
    REQUIRED_WW2 = tuple()

    def __init__(self, settings) -> None:
        self._settings = settings

    def get_path(self, key: str) -> str:
        return str(self._settings.value(key, "") or "").strip()

    def set_path(self, key: str, path: str) -> None:
        self._settings.setValue(key, str(path or "").strip())

    def validate_path(self, path: str) -> ValidationResult:
        raw = str(path or "").strip()
        if not raw:
            return ValidationResult(False, "empty")
        p = Path(raw)
        if not p.exists() or not p.is_dir():
            return ValidationResult(False, "missing")
        return ValidationResult(True, "ok")

    def path_status(self, key: str) -> ValidationResult:
        return self.validate_path(self.get_path(key))

    def ww1_ready(self) -> bool:
        return all(self.path_status(k).is_valid for k in self.REQUIRED_WW1)

    def ww2_ready(self) -> bool:
        if not self.REQUIRED_WW2:
            return False
        return all(self.path_status(k).is_valid for k in self.REQUIRED_WW2)

    def snapshot(self) -> Dict[str, str]:
        return {
            self.KEY_IL2_FC: self.get_path(self.KEY_IL2_FC),
            self.KEY_ROF: self.get_path(self.KEY_ROF),
            self.KEY_PWCG: self.get_path(self.KEY_PWCG),
        }
