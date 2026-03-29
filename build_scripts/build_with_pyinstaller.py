"""Build Wing Mate standalone executable via PyInstaller.

Usage:
  python build_scripts/build_with_pyinstaller.py
  python build_scripts/build_with_pyinstaller.py --clean --onefile
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def _asset_separator() -> str:
    return ";" if sys.platform.startswith("win") else ":"


def build(onefile: bool = True, clean: bool = True) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    main_py = repo_root / "main.py"
    assets_dir = repo_root / "app" / "assets"

    dist_dir = repo_root / "dist"
    build_dir = repo_root / "build"
    spec_file = repo_root / "WingMate.spec"

    if clean:
        shutil.rmtree(dist_dir, ignore_errors=True)
        shutil.rmtree(build_dir, ignore_errors=True)
        if spec_file.exists():
            spec_file.unlink()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--name",
        "WingMate",
        "--windowed",
    ]

    if onefile:
        cmd.append("--onefile")

    cmd.extend(
        [
            "--add-data",
            f"{assets_dir}{_asset_separator()}app/assets",
            str(main_py),
        ]
    )

    print("Running:", " ".join(cmd))
    return subprocess.call(cmd, cwd=repo_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Wing Mate executable using PyInstaller")
    parser.add_argument("--onefile", action="store_true", default=True, help="Generate one-file executable")
    parser.add_argument("--no-onefile", action="store_false", dest="onefile", help="Generate directory-based build")
    parser.add_argument("--clean", action="store_true", default=True, help="Clean previous build artifacts")
    parser.add_argument("--no-clean", action="store_false", dest="clean", help="Keep previous build artifacts")
    args = parser.parse_args()

    return build(onefile=args.onefile, clean=args.clean)


if __name__ == "__main__":
    raise SystemExit(main())
