from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional



@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    reason: str = ""


class AppConfig:
    """Gerencia caminhos de simuladores e validações por era."""

    KEY_IL2_FC = "paths/il2_fc"
    KEY_ROF = "paths/rof"
    KEY_PWCG = "paths/pwcg"
    KEY_PWCG_IL2 = "paths/pwcg_il2"
    KEY_PWCG_ROF = "paths/pwcg_rof"
    KEY_DATA_SOURCE = "data_source_mode"

    REQUIRED_WW1 = (KEY_IL2_FC, KEY_ROF)
    REQUIRED_WW2 = (KEY_IL2_FC,)
    WW2_MARKERS = ["BoS", "BoM", "BoK", "BoBP"]

    def __init__(self, settings) -> None:
        self._settings = settings

    def _safe_path(self, raw: str, must_exist: bool = True) -> Optional[Path]:
        value = str(raw or "").strip()
        if not value:
            return None

        try:
            path = Path(value).resolve()
        except (OSError, RuntimeError, ValueError) as exc:
            raise ValueError("invalid path") from exc

        if must_exist and (not path.exists() or not path.is_dir()):
            raise ValueError("path must be an existing directory")

        return path

    def get_path(self, key: str) -> str:
        return str(self._settings.value(key, "") or "").strip()

    @staticmethod
    def _normalize_data_source(mode: str) -> str:
        normalized = str(mode or "").strip().lower()
        if normalized in {"auto", "pwcg_json", "il2_vanilla"}:
            return normalized
        return "auto"

    def get_data_source(self) -> str:
        raw = str(self._settings.value(self.KEY_DATA_SOURCE, "auto") or "auto")
        return self._normalize_data_source(raw)

    def set_data_source(self, mode: str) -> None:
        self._settings.setValue(self.KEY_DATA_SOURCE, self._normalize_data_source(mode))

    def set_path(self, key: str, path: str) -> None:
        safe_path = self._safe_path(path)
        self._settings.setValue(key, str(safe_path) if safe_path else "")

    def validate_path(self, path: str) -> ValidationResult:
        if not str(path or "").strip():
            return ValidationResult(False, "empty")

        try:
            self._safe_path(path)
        except ValueError:
            return ValidationResult(False, "missing")

        return ValidationResult(True, "ok")

    def path_status(self, key: str) -> ValidationResult:
        return self.validate_path(self.get_path(key))

    def get_pwcg_path(self, simulator: str) -> str:
        """Retorna o caminho PWCG por simulador com fallback para chave legada."""
        sim = str(simulator or "").strip().lower()
        if sim == "il2":
            return self.get_path(self.KEY_PWCG_IL2) or self.get_path(self.KEY_PWCG)
        if sim == "rof":
            return self.get_path(self.KEY_PWCG_ROF) or self.get_path(self.KEY_PWCG)
        return self.get_path(self.KEY_PWCG)

    def ww1_ready(self) -> bool:
        return all(self.path_status(k).is_valid for k in self.REQUIRED_WW1)


    def _has_ww2_marker(self, base_path: Path) -> bool:
        markers = {m.upper() for m in self.WW2_MARKERS}

        for child in base_path.iterdir():
            name_upper = child.name.upper()
            stem_upper = child.stem.upper()
            if name_upper in markers or stem_upper in markers:
                return True
            if any(marker in name_upper for marker in markers):
                return True

        return False

    def ww2_ready(self) -> bool:
        if not all(self.path_status(k).is_valid for k in self.REQUIRED_WW2):
            return False

        il2_path = self._safe_path(self.get_path(self.KEY_IL2_FC))
        if il2_path is None:
            return False

        try:
            return self._has_ww2_marker(il2_path)
        except OSError:
            return False

    def snapshot(self) -> Dict[str, str]:
        return {
            self.KEY_IL2_FC: self.get_path(self.KEY_IL2_FC),
            self.KEY_ROF: self.get_path(self.KEY_ROF),
            self.KEY_PWCG: self.get_path(self.KEY_PWCG),
        }
