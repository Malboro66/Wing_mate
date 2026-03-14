# -*- coding: utf-8 -*-
"""
Wing Mate — tests/test_cp_db_integration.py

Testes unitários para a camada de infraestrutura do cp.db.
Utilizam banco em memória (`:memory:`) para não depender do arquivo real.
"""

from __future__ import annotations

import sqlite3
import struct
import tempfile
from pathlib import Path
from typing import Any, Dict
import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _create_test_db(path: Path) -> None:
    """Cria um cp.db mínimo com dados de teste."""
    conn = sqlite3.connect(str(path))
    conn.executescript("""
        CREATE TABLE career (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            personageId varchar(37) NOT NULL,
            playerId INTEGER NOT NULL DEFAULT 1,
            tvd INTEGER NOT NULL DEFAULT 28,
            currentDate datetime DEFAULT NULL,
            squadronId INTEGER NOT NULL DEFAULT 1,
            state INTEGER NOT NULL DEFAULT 1,
            insDate timestamp DEFAULT CURRENT_TIMESTAMP,
            isDeleted INTEGER NOT NULL DEFAULT 0,
            transferInfo varchar(512) NOT NULL DEFAULT '{}',
            startDate datetime DEFAULT NULL,
            uiData varchar(512) NOT NULL DEFAULT '{}',
            infoId varchar(32) NOT NULL DEFAULT '',
            phaseId varchar(32) NOT NULL DEFAULT '',
            neverBeCommander INTEGER NOT NULL DEFAULT 0,
            extends INTEGER NOT NULL DEFAULT 0,
            ironMan INTEGER NOT NULL DEFAULT 0,
            cuid varchar(37) NOT NULL DEFAULT 'test-cuid-001'
        );

        CREATE TABLE personage (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            personageId varchar(37) NOT NULL,
            tvd INTEGER NOT NULL DEFAULT 28,
            nickName varchar(64),
            firstName varchar(64),
            lastName varchar(64),
            insDate timestamp DEFAULT CURRENT_TIMESTAMP,
            isDeleted INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE pilot (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            squadronId INTEGER NOT NULL DEFAULT 1,
            personageId varchar(37) NOT NULL DEFAULT '',
            name varchar(128) NOT NULL DEFAULT '',
            rank varchar(64) DEFAULT NULL,
            rankId INTEGER NOT NULL DEFAULT 0,
            status INTEGER NOT NULL DEFAULT 0,
            country varchar(64) DEFAULT NULL,
            sortiesNum INTEGER NOT NULL DEFAULT 0,
            killLightPlane INTEGER NOT NULL DEFAULT 0,
            killLightFighter INTEGER NOT NULL DEFAULT 0,
            killMediumPlane INTEGER NOT NULL DEFAULT 0,
            killMediumFighter INTEGER NOT NULL DEFAULT 0,
            killHeavyPlane INTEGER NOT NULL DEFAULT 0,
            killStaticPlane INTEGER NOT NULL DEFAULT 0,
            killAssist INTEGER NOT NULL DEFAULT 0,
            insDate timestamp DEFAULT CURRENT_TIMESTAMP,
            isDeleted INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE mission (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            careerId INTEGER NOT NULL DEFAULT -1,
            date datetime DEFAULT NULL,
            airfield varchar(128) NOT NULL DEFAULT '',
            type varchar(64) DEFAULT NULL,
            insDate timestamp DEFAULT CURRENT_TIMESTAMP,
            isDeleted INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE sortie (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            missionId INTEGER NOT NULL DEFAULT -1,
            pilotId INTEGER NOT NULL DEFAULT -1,
            rankId INTEGER NOT NULL DEFAULT 0,
            pilotAi INTEGER NOT NULL DEFAULT 0,
            status INTEGER NOT NULL DEFAULT 0,
            score INTEGER NOT NULL DEFAULT 0,
            planeStatus INTEGER NOT NULL DEFAULT 0,
            model varchar(128) DEFAULT NULL,
            name varchar(128) DEFAULT NULL,
            killLightPlane INTEGER NOT NULL DEFAULT 0,
            killLightFighter INTEGER NOT NULL DEFAULT 0,
            killMediumPlane INTEGER NOT NULL DEFAULT 0,
            killAssist INTEGER NOT NULL DEFAULT 0,
            fkill INTEGER NOT NULL DEFAULT 0,
            flightTime INTEGER DEFAULT 0,
            date datetime DEFAULT NULL,
            insDate timestamp DEFAULT CURRENT_TIMESTAMP,
            isDeleted INTEGER DEFAULT 0
        );

        CREATE TABLE award (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            careerId INTEGER NOT NULL DEFAULT -1,
            type INTEGER NOT NULL DEFAULT 0,
            date datetime DEFAULT NULL,
            pilotId INTEGER NOT NULL DEFAULT 0,
            pilotName varchar(64) DEFAULT NULL,
            pilotRank INTEGER NOT NULL DEFAULT 0,
            squadName varchar(45) DEFAULT NULL,
            insDate timestamp DEFAULT CURRENT_TIMESTAMP,
            isDeleted INTEGER NOT NULL DEFAULT 0,
            PersonageId varchar(64) NOT NULL DEFAULT '',
            x varchar(50) NOT NULL DEFAULT '0.0',
            y varchar(50) NOT NULL DEFAULT '0.0',
            CausedByType INTEGER NOT NULL DEFAULT 0,
            CausedById varchar(64) DEFAULT NULL,
            "Show" INTEGER NOT NULL DEFAULT 0,
            SquadId INTEGER NOT NULL DEFAULT 0,
            squadConfigId INTEGER NOT NULL DEFAULT 0,
            GameTime datetime DEFAULT NULL,
            PersonageAwardId varchar(64) NOT NULL DEFAULT ''
        );

        CREATE TABLE ace (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            careerId INTEGER NOT NULL DEFAULT -1,
            name varchar(45) NOT NULL,
            deathDate datetime NOT NULL DEFAULT '1916-12-31',
            insDate timestamp DEFAULT CURRENT_TIMESTAMP,
            isDeleted INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE squadron (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            careerId INTEGER NOT NULL,
            configId INTEGER NOT NULL DEFAULT 1,
            airfield varchar(128) NOT NULL DEFAULT 'St. Omer',
            killAssist INTEGER NOT NULL DEFAULT 0,
            flightTime INTEGER NOT NULL DEFAULT 0,
            fkill INTEGER NOT NULL DEFAULT 0,
            score INTEGER NOT NULL DEFAULT 0,
            sorties INTEGER NOT NULL DEFAULT 0,
            goodSorties INTEGER NOT NULL DEFAULT 0,
            insDate timestamp DEFAULT CURRENT_TIMESTAMP,
            isDeleted INTEGER NOT NULL DEFAULT 0
        );

        -- Dados de teste
        INSERT INTO personage (personageId, tvd, nickName, firstName, lastName)
        VALUES ('test-personage-001', 28, 'Biggles', 'James', 'Bigglesworth');

        INSERT INTO career (personageId, squadronId, state, currentDate, startDate,
                            tvd, transferInfo, uiData, infoId, phaseId, cuid)
        VALUES ('test-personage-001', 1, 1,
                '1916-10-17 08:00:00', '1916-10-01 00:00:00',
                28, '{}', '{}', 'info1', 'phase1', 'cuid-001');

        INSERT INTO squadron (careerId, configId, airfield)
        VALUES (1, 1, 'St. Omer');

        INSERT INTO pilot (squadronId, personageId, name, rank, rankId, status,
                           country, sortiesNum, killLightFighter)
        VALUES (1, 'test-personage-001', 'Lt. James Bigglesworth',
                'Lieutenant', 3, 0, 'BRITAIN', 5, 3);

        INSERT INTO pilot (squadronId, personageId, name, rank, rankId, status,
                           country, sortiesNum)
        VALUES (1, 'npc-001', 'Sgt. Smith', 'Sergeant', 1, 0, 'BRITAIN', 8);

        INSERT INTO mission (careerId, date, airfield, type)
        VALUES (1, '1916-10-17 08:30:00', 'St. Omer', 'Patrol');

        INSERT INTO sortie (missionId, pilotId, status, model, killLightFighter,
                            flightTime, date)
        VALUES (1, 1, 0, 'Sopwith 1.5 Strutter', 1, 3600, '1916-10-17 08:30:00');

        INSERT INTO award (careerId, type, pilotId, pilotName)
        VALUES (1, 2, 1, 'Lt. James Bigglesworth');
    """)
    conn.commit()
    conn.close()


def _create_fake_scg_gtp(path: Path, squadron_names: Dict[int, str]) -> None:
    """Cria um Scg.gtp mínimo com uma entrada de squadrons-codes.cfg."""
    lines = ["// test catalog", ""]
    for squad_id, squad_name in squadron_names.items():
        lines.extend(
            [
                f"[Squadron={int(squad_id)}]",
                '\tname="' + str(squad_name) + '"',
                "[end]",
                "",
            ]
        )
    payload = ("\r\n".join(lines) + "\r\n").encode("utf-8")
    blob = b"STRMFILE" + (b"\x00" * 24) + payload

    entry_path = "/scg/99/squadrons-codes.cfg"
    path_bytes = entry_path.encode("utf-8")

    index_len = 8 + len(path_bytes) + 1 + 4 + 4 + 16
    data_offset = max(4096, index_len + 256)

    index = b"".join(
        [
            struct.pack("<I", len(path_bytes) + 1),
            struct.pack("<I", 0),
            path_bytes,
            b"\x00",
            b"FILE",
            struct.pack("<I", 1),
            struct.pack("<I", data_offset),
            struct.pack("<I", len(blob)),
            struct.pack("<I", 0),
            struct.pack("<I", len(payload)),
        ]
    )

    raw = bytearray()
    raw.extend(index)
    if len(raw) < data_offset:
        raw.extend(b"\x00" * (data_offset - len(raw)))
    raw.extend(blob)
    path.write_bytes(bytes(raw))


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "cp.db"
    _create_test_db(db_path)
    return db_path


# ---------------------------------------------------------------------------
# Testes: CpDbReader
# ---------------------------------------------------------------------------

class TestCpDbReader:
    def test_open_and_integrity(self, test_db):
        from app.infrastructure.cp_db_reader import CpDbReader
        with CpDbReader(test_db) as reader:
            assert reader.integrity_ok()

    def test_active_career(self, test_db):
        from app.infrastructure.cp_db_reader import CpDbReader
        with CpDbReader(test_db) as reader:
            career = reader.get_active_career()
        assert career is not None
        assert career["id"] == 1
        assert career["tvd"] == 28

    def test_personage(self, test_db):
        from app.infrastructure.cp_db_reader import CpDbReader
        with CpDbReader(test_db) as reader:
            p = reader.get_personage("test-personage-001")
        assert p is not None
        assert p["nickName"] == "Biggles"

    def test_player_pilot(self, test_db):
        from app.infrastructure.cp_db_reader import CpDbReader
        with CpDbReader(test_db) as reader:
            pilot = reader.get_player_pilot("test-personage-001")
        assert pilot is not None
        assert "Bigglesworth" in pilot["name"]

    def test_pilot_sorties(self, test_db):
        from app.infrastructure.cp_db_reader import CpDbReader
        with CpDbReader(test_db) as reader:
            sorties = reader.get_pilot_sorties(1)
        assert len(sorties) == 1
        assert sorties[0]["model"] == "Sopwith 1.5 Strutter"

    def test_awards(self, test_db):
        from app.infrastructure.cp_db_reader import CpDbReader
        with CpDbReader(test_db) as reader:
            awards = reader.get_awards(1)
        assert len(awards) == 1
        assert awards[0]["type"] == 2

    def test_award_binary_field_does_not_break_fetch(self, test_db):
        conn = sqlite3.connect(str(test_db))
        conn.execute(
            "UPDATE award SET PersonageAwardId=? WHERE id=1",
            (sqlite3.Binary(b"\x80\xff\x00AB"),),
        )
        conn.commit()
        conn.close()

        from app.infrastructure.cp_db_reader import CpDbReader

        with CpDbReader(test_db) as reader:
            rows = reader._rows("SELECT * FROM award WHERE id=1")

        assert len(rows) == 1
        assert "PersonageAwardId" in rows[0]
        assert isinstance(rows[0]["PersonageAwardId"], str)

    def test_soft_delete_filtered(self, test_db):
        """Registros deletados (isDeleted=1) não devem aparecer."""
        conn = sqlite3.connect(str(test_db))
        conn.execute("UPDATE pilot SET isDeleted=1 WHERE personageId='npc-001'")
        conn.commit()
        conn.close()

        from app.infrastructure.cp_db_reader import CpDbReader
        with CpDbReader(test_db) as reader:
            pilots = reader.get_pilots(1)
        assert all(p["isDeleted"] == 0 for p in pilots)


# ---------------------------------------------------------------------------
# Testes: CpDbMapper
# ---------------------------------------------------------------------------

class TestCpDbMapper:
    def test_career_to_campaign_dict(self):
        from app.infrastructure.cp_db_mapper import CpDbMapper
        career = {"id": 1, "personageId": "abc", "currentDate": "1916-10-17 08:00:00",
                  "squadronId": 1, "ironMan": 0}
        pilot = {"name": "Lt. Biggles", "country": "BRITAIN"}
        squad = {"airfield": "St. Omer"}
        result = CpDbMapper.career_to_campaign_dict(career, None, pilot, squad)
        assert result["pilot_name"] == "Lt. Biggles"
        assert result["squadron_name"] == "St. Omer"

    def test_pilot_to_pilot_data(self):
        from app.infrastructure.cp_db_mapper import CpDbMapper
        pilot = {"name": "Lt. Biggles", "rank": "Lieutenant", "country": "BRITAIN",
                 "killLightFighter": 3}
        sorties = [{"status": 0, "flightTime": 3600, "model": "Strutter",
                    "killLightFighter": 1}] * 3
        result = CpDbMapper.pilot_to_pilot_data(pilot, sorties, "No.45 Sqn")
        assert result["name"] == "Lt. Biggles"
        assert result["total_missions"] == 3
        assert result["total_victories"] == 3   # 3 sorties × 1 killLightFighter

    def test_pilot_morale_high_wins_applies_xp_multiplier(self):
        """Piloto com 5 vitórias seguidas deve ter morale > 80 e XP × 1.2."""
        from app.infrastructure.cp_db_mapper import CpDbMapper
        pilot = {"name": "Ace", "killLightFighter": 5}
        sorties = [
            {"status": 0, "killLightFighter": 1, "flightTime": 1800}
        ] * 5
        result = CpDbMapper.pilot_to_pilot_data(pilot, sorties, "No.1 Sqn")
        assert result["morale"] == 100
        assert result["xp_multiplier"] == 1.2
        assert result["xp"] == int(round(result["xp_base"] * 1.2))
        assert result["morale_mood"] == "🔥 Inspirado"
        assert result["needs_rest"] is False

    def test_pilot_morale_kia_streak_exhausted(self):
        """Piloto com 2 KIAs de ala deve ficar exausto (morale < 20)."""
        from app.infrastructure.cp_db_mapper import CpDbMapper
        pilot = {"name": "Tired", "killLightFighter": 0}
        sorties = [
            {"status": 1, "killLightFighter": 0, "flightTime": 600},
            {"status": 1, "killLightFighter": 0, "flightTime": 600},
            {"status": 0, "killLightFighter": 0, "flightTime": 600},
        ]
        result = CpDbMapper.pilot_to_pilot_data(pilot, sorties, "No.2 Sqn")
        assert result["morale"] == 0
        assert result["morale_state"] == "Exausto"
        assert result["morale_mood"] == "😵 Exausto"
        assert result["needs_rest"] is True
        assert result["xp_multiplier"] == 1.0

    def test_pilot_morale_neutral_no_multiplier(self):
        """Piloto sem eventos de moral relevantes mantém morale 50 e multiplier 1.0."""
        from app.infrastructure.cp_db_mapper import CpDbMapper
        pilot = {"name": "Average", "killLightFighter": 1}
        sorties = [{"status": 0, "killLightFighter": 0, "flightTime": 1200}] * 3
        result = CpDbMapper.pilot_to_pilot_data(pilot, sorties, "No.3 Sqn")
        assert result["morale"] == 50
        assert result["xp_multiplier"] == 1.0
        assert result["xp"] == result["xp_base"]

    def test_sorties_to_missions_date_format(self):
        from app.infrastructure.cp_db_mapper import CpDbMapper
        sorties = [{"missionId": 1, "status": 0, "model": "Strutter",
                    "date": "1916-10-17 08:30:00", "killLightFighter": 0,
                    "flightTime": 3600, "score": 100}]
        missions_by_id = {1: {"date": "1916-10-17 08:30:00", "airfield": "St. Omer", "type": "Patrol"}}
        result = CpDbMapper.sorties_to_missions(sorties, missions_by_id)
        assert result[0]["date"] == "17/10/1916"
        assert result[0]["time"] == "08:30"

    def test_awards_to_earned_ids(self):
        from app.infrastructure.cp_db_mapper import CpDbMapper
        awards = [{"type": 2}, {"type": 3}, {"type": 2}]
        ids = CpDbMapper.awards_to_earned_ids(awards)
        assert "iron_cross_2nd" in ids
        assert "pour_le_merite" in ids
        assert len(ids) == 2  # deduplicados

    def test_pilots_to_squadron_status_mapping(self):
        from app.infrastructure.cp_db_mapper import CpDbMapper
        pilots = [
            {"name": "A", "rank": "Lt", "status": 0, "killLightFighter": 2, "sortiesNum": 5},
            {"name": "B", "rank": "Sgt", "status": 2, "killLightFighter": 0, "sortiesNum": 3},
        ]
        result = CpDbMapper.pilots_to_squadron(pilots)
        statuses = {p["name"]: p["status"] for p in result}
        assert statuses["A"] == "Ativo"
        assert "KIA" in statuses["B"]

    def test_aircraft_progression_badge(self):
        from app.infrastructure.cp_db_mapper import CpDbMapper
        sorties = [{"model": "Strutter", "killLightFighter": 2, "killMediumFighter": 3}] * 3
        prog = CpDbMapper.sorties_to_aircraft_progression(sorties)
        assert prog["Strutter"]["badge"] == "Ás do Modelo"  # 15 vitórias >= 5


# ---------------------------------------------------------------------------
# Testes: CpDbCampaignRepository (integração com banco real)
# ---------------------------------------------------------------------------

class TestCpDbCampaignRepository:
    def test_get_campaign(self, test_db):
        from app.infrastructure.cp_db_repository import CpDbCampaignRepository
        repo = CpDbCampaignRepository(test_db)
        campaign = repo.get_campaign("1")
        assert campaign is not None
        assert campaign.name == "1"
        assert campaign.squadron_name == "St. Omer"

    def test_get_campaign_active(self, test_db):
        from app.infrastructure.cp_db_repository import CpDbCampaignRepository
        repo = CpDbCampaignRepository(test_db)
        campaign = repo.get_campaign("active")
        # "active" não é dígito → busca carreira ativa
        assert campaign is not None

    def test_get_missions(self, test_db):
        from app.infrastructure.cp_db_repository import CpDbCampaignRepository
        repo = CpDbCampaignRepository(test_db)
        missions = repo.get_missions("1", "")
        assert len(missions) == 1
        assert missions[0]["aircraft"] == "Sopwith 1.5 Strutter"

    def test_process_career_full(self, test_db):
        from app.infrastructure.cp_db_repository import CpDbCampaignRepository
        repo = CpDbCampaignRepository(test_db)
        data = repo.process_career("1")
        assert "pilot" in data
        assert "missions" in data
        assert "squadron" in data
        assert data["pilot"]["name"] == "Lt. James Bigglesworth"
        assert len(data["missions"]) == 1

    def test_process_career_enriches_ace_country_by_name(self, test_db):
        conn = sqlite3.connect(str(test_db))
        conn.execute(
            "INSERT INTO ace (careerId, name, deathDate, isDeleted) VALUES (?, ?, ?, ?)",
            (1, "Lt. James Bigglesworth", "1916-12-31", 0),
        )
        conn.commit()
        conn.close()

        from app.infrastructure.cp_db_repository import CpDbCampaignRepository

        repo = CpDbCampaignRepository(test_db)
        data = repo.process_career("1")

        assert data.get("aces")
        ace = data["aces"][0]
        assert ace["name"] == "Lt. James Bigglesworth"
        assert ace["country"] == "BRITAIN"

    def test_process_career_uses_award_squad_name_fallback(self, test_db):
        conn = sqlite3.connect(str(test_db))
        conn.execute(
            "UPDATE award SET squadName='No.45 Squadron', SquadId=1, squadConfigId=1 WHERE id=1"
        )
        conn.commit()
        conn.close()

        from app.infrastructure.cp_db_repository import CpDbCampaignRepository

        repo = CpDbCampaignRepository(test_db)
        data = repo.process_career("1")
        assert data["pilot"]["squadron"] == "No.45 Squadron"

    def test_list_career_ids(self, test_db):
        from app.infrastructure.cp_db_repository import CpDbCampaignRepository
        repo = CpDbCampaignRepository(test_db)
        ids = repo.list_career_ids()
        assert "1" in ids

    def test_earned_medal_ids(self, test_db):
        from app.infrastructure.cp_db_repository import CpDbCampaignRepository
        repo = CpDbCampaignRepository(test_db)
        ids = repo.get_earned_medal_ids("1")
        assert "iron_cross_2nd" in ids

    def test_missing_db_raises(self, tmp_path):
        from app.infrastructure.cp_db_repository import CpDbCampaignRepository
        repo = CpDbCampaignRepository(tmp_path / "nao_existe.db")
        # Deve retornar None/[] sem explodir a aplicação
        assert repo.get_campaign("1") is None
        assert repo.get_missions("1", "") == []


# ---------------------------------------------------------------------------
# Testes: AppContainer (detecção automática)
# ---------------------------------------------------------------------------

class TestAppContainerCpDb:
    def test_has_cp_db_false_by_default(self):
        from app.application.container import AppContainer
        container = AppContainer()
        assert not container.has_cp_db()

    def test_set_cp_db_path(self, test_db):
        from app.application.container import AppContainer
        container = AppContainer()
        container.set_cp_db_path(test_db)
        assert container.has_cp_db()

    def test_list_campaigns_uses_db(self, test_db):
        from app.application.container import AppContainer
        container = AppContainer()
        container.set_cp_db_path(test_db)
        campaigns = container.list_campaigns()
        assert "1" in campaigns

    def test_process_campaign_uses_db(self, test_db):
        from app.application.container import AppContainer
        container = AppContainer()
        container.set_cp_db_path(test_db)
        data = container.process_campaign("1")
        assert data.get("pilot", {}).get("name") == "Lt. James Bigglesworth"

    def test_auto_detection(self, tmp_path, test_db):
        """cp.db na raiz do caminho deve ser detectado automaticamente."""
        import shutil
        from app.application.container import AppContainer

        # Copia o db para simular presença na pasta do simulador
        simulator_dir = tmp_path / "simulator_root"
        simulator_dir.mkdir(parents=True, exist_ok=True)
        dest = simulator_dir / "cp.db"
        shutil.copy(test_db, dest)

        container = AppContainer()
        container.set_pwcgfc_path(str(simulator_dir))
        assert container.has_cp_db()

    def test_source_mode_pwcg_json_disables_auto_cp_db_detection(self, tmp_path, test_db):
        import shutil
        from app.application.container import AppContainer

        simulator_dir = tmp_path / "simulator_root"
        simulator_dir.mkdir(parents=True, exist_ok=True)
        dest = simulator_dir / "cp.db"
        shutil.copy(test_db, dest)

        container = AppContainer()
        container.set_source_mode(AppContainer.SOURCE_PWCG_JSON)
        container.set_pwcgfc_path(str(simulator_dir))

        assert not container.has_cp_db()

    def test_source_mode_vanilla_enables_auto_cp_db_detection(self, tmp_path, test_db):
        import shutil
        from app.application.container import AppContainer

        simulator_dir = tmp_path / "simulator_root"
        simulator_dir.mkdir(parents=True, exist_ok=True)
        dest = simulator_dir / "cp.db"
        shutil.copy(test_db, dest)

        container = AppContainer()
        container.set_source_mode(AppContainer.SOURCE_IL2_VANILLA)
        container.set_pwcgfc_path(str(simulator_dir))

        assert container.has_cp_db()


# ---------------------------------------------------------------------------
# Testes: Vanilla FlightLogs (missionReport .mlg)
# ---------------------------------------------------------------------------

class TestVanillaMissionReportReader:
    def test_reader_extracts_summary(self, tmp_path):
        from app.infrastructure.vanilla_mission_report import VanillaMissionReportReader

        career_dir = tmp_path / "data" / "Career"
        logs_dir = tmp_path / "data" / "FlightLogs"
        career_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)

        db_path = career_dir / "cp.db"
        db_path.write_bytes(b"SQLite format 3")

        report_path = logs_dir / "missionReport(2026-03-07_16-09-50).mlg"
        report_path.write_bytes(
            b"\x00Sopwith Strutter\x00James Fisher\x00BotPilot_Spad13_RAF17\x00"
        )

        reader = VanillaMissionReportReader(db_path)
        summary = reader.build_latest_report_summary()

        assert summary is not None
        assert "Sopwith Strutter" in summary

    def test_repo_enriches_latest_mission_with_flightlog(self, tmp_path, test_db):
        import shutil

        from app.infrastructure.cp_db_repository import CpDbCampaignRepository

        career_dir = tmp_path / "data" / "Career"
        logs_dir = tmp_path / "data" / "FlightLogs"
        career_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)

        db_path = career_dir / "cp.db"
        shutil.copy(test_db, db_path)

        report_path = logs_dir / "missionReport(2026-03-07_16-09-50).mlg"
        report_path.write_bytes(
            b"\x00Sopwith Strutter\x00James Fisher\x00BotPilot_Spad13_RAF17\x00"
        )

        repo = CpDbCampaignRepository(db_path)
        data = repo.process_career("1")

        assert data.get("missions")
        description = data["missions"][-1]["description"]
        assert "[FlightLogs]" in description
        assert "Sopwith Strutter" in description

    def test_repo_enriches_all_missions_with_matching_flightlogs(self, tmp_path, test_db):
        import shutil
        import sqlite3

        from app.infrastructure.cp_db_repository import CpDbCampaignRepository

        career_dir = tmp_path / "data" / "Career"
        logs_dir = tmp_path / "data" / "FlightLogs"
        career_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)

        db_path = career_dir / "cp.db"
        shutil.copy(test_db, db_path)

        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO mission (careerId, date, airfield, type) VALUES (?, ?, ?, ?)",
            (1, "1916-10-18 09:15:00", "St. Omer", "Escort"),
        )
        conn.execute(
            "INSERT INTO sortie (missionId, pilotId, status, model, killLightFighter, flightTime, date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (2, 1, 0, "Sopwith 1.5 Strutter", 0, 2400, "1916-10-18 09:15:00"),
        )
        conn.commit()
        conn.close()

        (logs_dir / "missionReport(1916-10-17_08-30-00).mlg").write_bytes(b"\x00First Mission Pilot\x00")
        (logs_dir / "missionReport(1916-10-18_09-15-00).mlg").write_bytes(b"\x00Second Mission Pilot\x00")

        repo = CpDbCampaignRepository(db_path)
        data = repo.process_career("1")

        assert len(data.get("missions", [])) >= 2
        descriptions = [m.get("description", "") for m in data["missions"]]
        assert any("First Mission Pilot" in d for d in descriptions)
        assert any("Second Mission Pilot" in d for d in descriptions)


class TestVanillaSquadronCatalog:
    def test_catalog_reads_name_from_scg_gtp(self, tmp_path):
        from app.infrastructure.vanilla_squadron_catalog import VanillaSquadronCatalog

        career_dir = tmp_path / "data" / "Career"
        career_dir.mkdir(parents=True)
        db_path = career_dir / "cp.db"
        db_path.write_bytes(b"SQLite format 3")

        scg_path = tmp_path / "data" / "Scg.gtp"
        _create_fake_scg_gtp(scg_path, {302045: "No.45 Squadron"})

        catalog = VanillaSquadronCatalog(db_path)
        assert catalog.get_name(302045) == "No.45 Squadron"


class TestIL2DataParserPathResolution:
    def test_parser_accepts_user_campaigns_path(self, tmp_path):
        from app.core.data_parser import IL2DataParser

        campaigns_dir = tmp_path / "PWCGFC" / "User" / "Campaigns"
        (campaigns_dir / "Campaign A").mkdir(parents=True)

        parser = IL2DataParser(campaigns_dir)
        campaigns = parser.get_campaigns()

        assert parser.campaigns_path == campaigns_dir
        assert "Campaign A" in campaigns

    def test_parser_accepts_single_campaign_directory(self, tmp_path):
        from app.core.data_parser import IL2DataParser

        campaign_dir = tmp_path / "PWCGFC" / "User" / "Campaigns" / "Campaign B"
        campaign_dir.mkdir(parents=True)
        (campaign_dir / "Campaign.json").write_text("{}", encoding="utf-8")

        parser = IL2DataParser(campaign_dir)
        campaigns = parser.get_campaigns()

        assert parser.campaigns_path == campaign_dir.parent
        assert "Campaign B" in campaigns
