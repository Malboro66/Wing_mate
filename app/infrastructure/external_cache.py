from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional


class ExternalCache:
    """Cache local em SQLite para dados externos com controle de TTL."""

    def __init__(self, db_path: Optional[Path | str] = None, default_ttl_days: int = 30) -> None:
        self._db_path = Path(db_path) if db_path else Path(__file__).resolve().with_name("external_cache.db")
        self._default_ttl_days = int(default_ttl_days) if int(default_ttl_days) > 0 else 30
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS external_cache (
                    key TEXT PRIMARY KEY,
                    payload TEXT,
                    source TEXT,
                    fetched REAL,
                    ttl_days INTEGER DEFAULT 30
                )
                """
            )
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        normalized_key = str(key or "").strip()
        if not normalized_key:
            return None

        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM external_cache WHERE key = ?",
                (normalized_key,),
            ).fetchone()

        if not row:
            return None

        payload = str(row["payload"] or "")
        if not payload:
            return None

        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None

    def set(self, key: str, data: Any, source: str) -> None:
        normalized_key = str(key or "").strip()
        if not normalized_key:
            raise ValueError("cache key cannot be empty")

        payload = json.dumps(data, ensure_ascii=False)
        fetched = float(time.time())
        source_value = str(source or "").strip()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO external_cache (key, payload, source, fetched, ttl_days)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    payload = excluded.payload,
                    source = excluded.source,
                    fetched = excluded.fetched,
                    ttl_days = excluded.ttl_days
                """,
                (normalized_key, payload, source_value, fetched, self._default_ttl_days),
            )
            conn.commit()

    def is_stale(self, key: str) -> bool:
        normalized_key = str(key or "").strip()
        if not normalized_key:
            return True

        with self._connect() as conn:
            row = conn.execute(
                "SELECT fetched, ttl_days FROM external_cache WHERE key = ?",
                (normalized_key,),
            ).fetchone()

        if not row:
            return True

        fetched_raw = row["fetched"]
        ttl_raw = row["ttl_days"]

        fetched = float(fetched_raw) if fetched_raw is not None else 0.0
        ttl_days = int(ttl_raw) if ttl_raw is not None else self._default_ttl_days
        if ttl_days <= 0:
            return True

        ttl_seconds = ttl_days * 86400
        return (time.time() - fetched) > ttl_seconds
