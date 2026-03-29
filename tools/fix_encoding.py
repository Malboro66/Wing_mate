#!/usr/bin/env python3
"""Repair UTF-8 mojibake in Python source files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

# Keep double-mojibake replacements before single-mojibake replacements.
DOUBLE_MOJIBAKE_REPLACEMENTS: list[tuple[str, str]] = [
    ("ÃƒÂ¡", "á"),
    ("ÃƒÂ¢", "â"),
    ("ÃƒÂ£", "ã"),
    ("ÃƒÂ§", "ç"),
    ("ÃƒÂ©", "é"),
    ("ÃƒÂª", "ê"),
    ("ÃƒÂ­", "í"),
    ("ÃƒÂ³", "ó"),
    ("ÃƒÂ´", "ô"),
    ("ÃƒÂµ", "õ"),
    ("ÃƒÂº", "ú"),
    ("ÃƒÂ", "Á"),
    ("ÃƒÂ‰", "É"),
    ("ÃƒÂ“", "Ó"),
    ("ÃƒÂ", "Í"),
    ("ÃƒÂ‡", "Ç"),
    ("Ã‚Â", ""),
]

SINGLE_MOJIBAKE_REPLACEMENTS: list[tuple[str, str]] = [
    ("â€”", "—"),
    ("â€“", "–"),
    ("â€˜", "‘"),
    ("â€™", "’"),
    ("â€œ", "“"),
    ("â€\x9d", "”"),
    ("â€¦", "…"),
    ("â€¢", "•"),
    ("Ã¡", "á"),
    ("Ã¢", "â"),
    ("Ã£", "ã"),
    ("Ã§", "ç"),
    ("Ã©", "é"),
    ("Ãª", "ê"),
    ("Ã­", "í"),
    ("Ã³", "ó"),
    ("Ã´", "ô"),
    ("Ãµ", "õ"),
    ("Ãº", "ú"),
    ("Ã", "Á"),
    ("Ã‰", "É"),
    ("Ã“", "Ó"),
    ("Ã", "Í"),
    ("Ã‡", "Ç"),
    ("ÃŸ", "ß"),
    ("NÃƒO", "NÃO"),
    ("nÃƒo", "não"),
    ("Ã¢â‚¬â€", "—"),
    ("Ã¢â‚¬â€œ", "–"),
    ("Ã¢â‚¬â„¢", "’"),
    ("Ã¢â‚¬Å“", "“"),
    ("Ã¢â‚¬Â¦", "…"),
    ("Ã¯Â»Â¿", ""),
    ("ðŸ”¥", "🔥"),
    ("ðŸ˜", "😐"),
    ("ðŸ—ž️", "🗞️"),
    ("Â", ""),
]

REPLACEMENTS = DOUBLE_MOJIBAKE_REPLACEMENTS + SINGLE_MOJIBAKE_REPLACEMENTS


def read_text_with_fallback(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("cp1252"), "cp1252"


def repair_text(text: str) -> tuple[str, int]:
    substitutions = 0
    for old, new in REPLACEMENTS:
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            substitutions += count
    return text, substitutions


def iter_py_files(paths: Iterable[Path]) -> Iterable[Path]:
    for base in paths:
        if base.is_file() and base.suffix == ".py":
            yield base
            continue
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if ".git" in path.parts:
                continue
            yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair mojibake in .py files")
    parser.add_argument("paths", nargs="*", default=["."], help="Files/folders to process")
    parser.add_argument("--dry-run", action="store_true", help="Report changes only")
    args = parser.parse_args()

    changed_files = 0
    changed_subs = 0
    for path in iter_py_files([Path(p) for p in args.paths]):
        original, codec = read_text_with_fallback(path)
        fixed, subs = repair_text(original)
        if subs == 0 or fixed == original:
            continue

        changed_files += 1
        changed_subs += subs
        print(f"{path} [{codec}] -> {subs} substitutions")
        if not args.dry_run:
            path.write_text(fixed, encoding="utf-8", newline="\n")

    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(f"{mode}: changed_files={changed_files}, substitutions={changed_subs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
