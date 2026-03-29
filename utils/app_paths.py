from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "WingMate"


def get_app_data_dir() -> Path:
    """Return a user-scoped writable data directory for Wing Mate."""
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")

    path = base / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logs_dir() -> Path:
    path = get_app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_observability_dir() -> Path:
    path = get_logs_dir() / "observability"
    path.mkdir(parents=True, exist_ok=True)
    return path
