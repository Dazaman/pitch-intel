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


def test_compare_players():
    conn = _setup_test_db()
    for pid, name, goals in [("reep_p1", "Cole Palmer", 22), ("reep_p2", "Bukayo Saka", 16)]:
        conn.execute(
            "INSERT INTO people (reep_id, type, name) VALUES (?, ?, ?)", (pid, "player", name)
        )
        conn.execute(
            """INSERT INTO player_season_stats (reep_id, season, league, source, goals)
               VALUES (?, ?, ?, ?, ?)""",
            (pid, "2024-2025", "Premier League", "fbref", goals),
        )
    conn.commit()
    client = TestClient(app)
    resp = client.get("/api/compare/players?ids=reep_p1,reep_p2")
    assert resp.status_code == 200
    data = resp.json()
    assert "reep_p1" in data
    assert "reep_p2" in data
    assert data["reep_p1"]["name"] == "Cole Palmer"
    assert data["reep_p2"]["name"] == "Bukayo Saka"


def test_compare_teams():
    conn = _setup_test_db()
    for tid, name, wins in [("reep_t1", "Arsenal", 25), ("reep_t2", "Chelsea", 20)]:
        conn.execute("INSERT INTO teams (reep_id, name) VALUES (?, ?)", (tid, name))
        conn.execute(
            """INSERT INTO team_season_stats (reep_id, season, league, source, wins)
               VALUES (?, ?, ?, ?, ?)""",
            (tid, "2024-2025", "Premier League", "understat", wins),
        )
    conn.commit()
    client = TestClient(app)
    resp = client.get("/api/compare/teams?ids=reep_t1,reep_t2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["reep_t1"]["name"] == "Arsenal"
    assert data["reep_t2"]["name"] == "Chelsea"
