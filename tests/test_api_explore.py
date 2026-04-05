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


def _seed_per90(conn):
    conn.execute(
        "INSERT INTO people (reep_id, type, name, position) VALUES (?, ?, ?, ?)",
        ("reep_p1", "player", "Cole Palmer", "attacking midfielder"),
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
           VALUES (?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?, ?, ?, ?,
                   ?, ?, ?, ?,
                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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


def test_scatter_basic():
    conn = _setup_test_db()
    _seed_per90(conn)
    client = TestClient(app)
    resp = client.get("/api/explore/scatter?x=goals_per90&y=xg_per90")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Cole Palmer"
    assert data[0]["x_value"] == 0.73
    assert data[0]["y_value"] == 0.62


def test_scatter_filter_by_league():
    conn = _setup_test_db()
    _seed_per90(conn)
    client = TestClient(app)
    resp = client.get("/api/explore/scatter?x=goals_per90&y=xg_per90&league=La Liga")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 0


def test_scatter_invalid_stat():
    _setup_test_db()
    client = TestClient(app)
    resp = client.get("/api/explore/scatter?x=goals_per90&y=invalid_stat")
    assert resp.status_code == 400
