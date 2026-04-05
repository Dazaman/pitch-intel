from fastapi.testclient import TestClient

from api.app import app
from api.deps import override_db


def _setup_test_db():
    import sqlite3

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    from pipeline.db import init_schema

    init_schema(conn)
    override_db(conn)
    return conn


def _seed_player(conn):
    conn.execute(
        """INSERT INTO people (reep_id, type, name, full_name, nationality, position, height_cm)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            "reep_p1",
            "player",
            "Cole Palmer",
            "Cole Jermaine Palmer",
            "United Kingdom",
            "attacking midfielder",
            185,
        ),
    )
    conn.execute(
        """INSERT INTO player_season_stats
           (reep_id, season, league, source, minutes_played, games, goals, assists, xg, xa)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("reep_p1", "2024-2025", "Premier League", "fbref", 2700, 32, 22, 11, 18.5, 9.8),
    )
    conn.execute(
        """INSERT INTO shots
           (id, reep_id, season, league, minute, result, x, y, xg, situation, shot_type, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            501,
            "reep_p1",
            "2024-2025",
            "Premier League",
            23,
            "Goal",
            0.89,
            0.45,
            0.76,
            "OpenPlay",
            "RightFoot",
            "understat",
        ),
    )
    conn.execute(
        """INSERT INTO player_per90
           (reep_id, season, league, position_group, minutes_played,
            goals_per90, xg_per90, assists_per90, xa_per90,
            shots_per90, key_passes_per90, progressive_passes_per90, progressive_carries_per90,
            tackles_per90, interceptions_per90, pressures_per90, take_ons_per90,
            goals_pctile, xg_pctile, assists_pctile, xa_pctile,
            shots_pctile, key_passes_pctile, progressive_passes_pctile, progressive_carries_pctile,
            tackles_pctile, interceptions_pctile, pressures_pctile, take_ons_pctile)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?)""",
        (
            "reep_p1",
            "2024-2025",
            "Premier League",
            "MF",
            2700,
            0.73,
            0.62,
            0.37,
            0.33,
            2.67,
            1.67,
            2.33,
            1.83,
            0.67,
            0.5,
            5.0,
            1.33,
            95,
            90,
            88,
            85,
            92,
            80,
            78,
            75,
            30,
            25,
            40,
            70,
        ),
    )
    conn.commit()


def test_get_player():
    conn = _setup_test_db()
    _seed_player(conn)
    client = TestClient(app)
    resp = client.get("/api/player/reep_p1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Cole Palmer"
    assert data["height_cm"] == 185


def test_get_player_not_found():
    _setup_test_db()
    client = TestClient(app)
    resp = client.get("/api/player/reep_pXXXXXX")
    assert resp.status_code == 404


def test_get_player_stats():
    conn = _setup_test_db()
    _seed_player(conn)
    client = TestClient(app)
    resp = client.get("/api/player/reep_p1/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["goals"] == 22
    assert data[0]["xg"] == 18.5


def test_get_player_shots():
    conn = _setup_test_db()
    _seed_player(conn)
    client = TestClient(app)
    resp = client.get("/api/player/reep_p1/shots?season=2024-2025")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["result"] == "Goal"
    assert data[0]["xg"] == 0.76


def test_get_player_radar():
    conn = _setup_test_db()
    _seed_player(conn)
    client = TestClient(app)
    resp = client.get("/api/player/reep_p1/radar")
    assert resp.status_code == 200
    data = resp.json()
    assert data["position_group"] == "MF"
    assert data["stats"]["goals_per90"] == 0.73
    assert data["percentiles"]["goals_pctile"] == 95
