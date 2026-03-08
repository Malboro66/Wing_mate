# -*- coding: utf-8 -*-
"""
Wing Mate — app/infrastructure/cp_db_reader.py

Leitor de baixo nível para o banco SQLite `cp.db` do IL-2 Flying Circus.

Responsabilidades:
  - Abrir conexão read-only (uri=True, ?mode=ro)
  - Aplicar PRAGMA WAL e foreign_keys
  - Fornecer métodos de consulta tipados com soft-delete embutido
  - Não conhecer domínio — retorna apenas dicts/listas
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("IL2CampaignAnalyzer")


class CpDbReader:
    """Abstração de acesso read-only ao cp.db."""

    # Código TVD do Flying Circus (conforme relatório forense)
    TVD_FLYING_CIRCUS = 28

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------ #
    # Conexão                                                              #
    # ------------------------------------------------------------------ #

    def open(self) -> None:
        """Abre conexão read-only com WAL habilitado."""
        if self._conn is not None:
            return

        uri = self._db_path.as_uri() + "?mode=ro"
        try:
            self._conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            # NOTA: NÃO executar PRAGMA journal_mode=WAL em conexão read-only
            # (gera "attempt to write a readonly database").
            # O banco usa DELETE mode (padrão do jogo) — leituras são seguras.
            self._conn.execute("PRAGMA foreign_keys=OFF;")  # sem FKs declarativas
            logger.info("cp.db aberto: %s", self._db_path)
        except sqlite3.OperationalError as exc:
            self._conn = None
            raise ConnectionError(f"Não foi possível abrir cp.db: {exc}") from exc

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "CpDbReader":
        self.open()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------ #
    # Utilitário                                                           #
    # ------------------------------------------------------------------ #

    def _rows(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Executa query e retorna lista de dicts. Garante conexão aberta."""
        if self._conn is None:
            self.open()
        cur = self._conn.execute(sql, params)  # type: ignore[union-attr]
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def _one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        rows = self._rows(sql, params)
        return rows[0] if rows else None

    # ------------------------------------------------------------------ #
    # career                                                               #
    # ------------------------------------------------------------------ #

    def get_active_career(self, career_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retorna carreira ativa (state=1) ou a carreira pelo id."""
        if career_id is not None:
            return self._one(
                "SELECT * FROM career WHERE id=? AND isDeleted=0 LIMIT 1",
                (career_id,),
            )
        return self._one(
            "SELECT * FROM career WHERE isDeleted=0 AND state=1 ORDER BY id DESC LIMIT 1"
        )

    def list_careers(self) -> List[Dict[str, Any]]:
        """Lista todas as carreiras não deletadas."""
        return self._rows(
            "SELECT id, cuid, currentDate, tvd, squadronId, state, startDate, ironMan "
            "FROM career WHERE isDeleted=0 ORDER BY id DESC"
        )

    # ------------------------------------------------------------------ #
    # personage                                                            #
    # ------------------------------------------------------------------ #

    def get_personage(self, personage_id: str) -> Optional[Dict[str, Any]]:
        return self._one(
            "SELECT * FROM personage WHERE personageId=? AND isDeleted=0 LIMIT 1",
            (personage_id,),
        )

    # ------------------------------------------------------------------ #
    # pilot                                                                #
    # ------------------------------------------------------------------ #

    def get_pilots(self, squadron_id: int) -> List[Dict[str, Any]]:
        """Todos os pilotos ativos de um esquadrão (isDeleted=0)."""
        return self._rows(
            "SELECT * FROM pilot WHERE squadronId=? AND isDeleted=0 ORDER BY id",
            (squadron_id,),
        )

    def get_player_pilot(self, personage_id: str) -> Optional[Dict[str, Any]]:
        """Piloto do jogador identificado pelo personageId."""
        return self._one(
            "SELECT * FROM pilot WHERE personageId=? AND isDeleted=0 LIMIT 1",
            (personage_id,),
        )

    # ------------------------------------------------------------------ #
    # mission                                                              #
    # ------------------------------------------------------------------ #

    def get_missions(self, career_id: int) -> List[Dict[str, Any]]:
        """Missões de uma carreira, ordenadas por data (mais antiga primeiro)."""
        return self._rows(
            "SELECT * FROM mission WHERE careerId=? AND isDeleted=0 ORDER BY date ASC",
            (career_id,),
        )

    def get_mission(self, mission_id: int) -> Optional[Dict[str, Any]]:
        return self._one(
            "SELECT * FROM mission WHERE id=? AND isDeleted=0 LIMIT 1",
            (mission_id,),
        )

    # ------------------------------------------------------------------ #
    # sortie                                                               #
    # ------------------------------------------------------------------ #

    def get_sorties(self, mission_id: int) -> List[Dict[str, Any]]:
        return self._rows(
            "SELECT * FROM sortie WHERE missionId=? AND isDeleted=0 ORDER BY id",
            (mission_id,),
        )

    def get_pilot_sorties(self, pilot_id: int) -> List[Dict[str, Any]]:
        """Todas as saídas de um piloto específico."""
        return self._rows(
            "SELECT * FROM sortie WHERE pilotId=? AND isDeleted=0 ORDER BY date ASC",
            (pilot_id,),
        )

    # ------------------------------------------------------------------ #
    # award (medalhas)                                                     #
    # ------------------------------------------------------------------ #

    def get_awards(self, career_id: int) -> List[Dict[str, Any]]:
        return self._rows(
            "SELECT * FROM award WHERE careerId=? AND isDeleted=0 ORDER BY date",
            (career_id,),
        )

    def get_pilot_awards(self, pilot_id: int) -> List[Dict[str, Any]]:
        return self._rows(
            "SELECT * FROM award WHERE pilotId=? AND isDeleted=0 ORDER BY date",
            (pilot_id,),
        )

    # ------------------------------------------------------------------ #
    # event                                                                #
    # ------------------------------------------------------------------ #

    def get_events(self, career_id: int) -> List[Dict[str, Any]]:
        return self._rows(
            "SELECT * FROM event WHERE careerId=? AND isDeleted=0 ORDER BY date",
            (career_id,),
        )

    # ------------------------------------------------------------------ #
    # squadron                                                             #
    # ------------------------------------------------------------------ #

    def get_squadron(self, squadron_id: int) -> Optional[Dict[str, Any]]:
        return self._one(
            "SELECT * FROM squadron WHERE id=? AND isDeleted=0 LIMIT 1",
            (squadron_id,),
        )

    # ------------------------------------------------------------------ #
    # ace                                                                  #
    # ------------------------------------------------------------------ #

    def get_aces(self, career_id: int) -> List[Dict[str, Any]]:
        return self._rows(
            "SELECT * FROM ace WHERE careerId=? AND isDeleted=0 ORDER BY id",
            (career_id,),
        )

    # ------------------------------------------------------------------ #
    # plane                                                                #
    # ------------------------------------------------------------------ #

    def get_planes(self, squadron_id: int) -> List[Dict[str, Any]]:
        return self._rows(
            "SELECT * FROM plane WHERE squadronId=? AND isDeleted=0",
            (squadron_id,),
        )

    # ------------------------------------------------------------------ #
    # Verificação                                                          #
    # ------------------------------------------------------------------ #

    def integrity_ok(self) -> bool:
        row = self._one("PRAGMA integrity_check")
        return bool(row) and list(row.values())[0] == "ok"
