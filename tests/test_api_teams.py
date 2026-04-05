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


def test_get_team():
    conn = _setup_test_db()
    conn.execute(
        "INSERT INTO teams (reep_id, name, country, stadium) VALUES (?, ?, ?, ?)",
        ("reep_t1", "Arsenal F.C.", "United Kingdom", "Emirates Stadium"),
    )
    conn.commit()
    client = TestClient(app)
    resp = client.get("/api/team/reep_t1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Arsenal F.C."
    assert data["stadium"] == "Emirates Stadium"


def test_get_team_not_found():
    _setup_test_db()
    client = TestClient(app)
    resp = client.get("/api/team/reep_tXXXXXX")
    assert resp.status_code == 404


def test_get_team_stats():
    conn = _setup_test_db()
    conn.execute("INSERT INTO teams (reep_id, name) VALUES (?, ?)", ("reep_t1", "Arsenal F.C."))
    conn.execute(
        """INSERT INTO team_season_stats
           (reep_id, season, league, source, wins, draws, losses,
            goals_for, goals_against, xg, xga, ppda)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("reep_t1", "2024-2025", "Premier League", "understat", 25, 8, 5, 80, 35, 78.5, 33.2, 8.5),
    )
    conn.commit()
    client = TestClient(app)
    resp = client.get("/api/team/reep_t1/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["wins"] == 25
    assert data[0]["xg"] == 78.5


def test_get_team_squad():
    conn = _setup_test_db()
    conn.execute("INSERT INTO teams (reep_id, name) VALUES (?, ?)", ("reep_t1", "Arsenal"))
    conn.execute(
        "INSERT INTO people (reep_id, type, name, position, nationality) VALUES (?, ?, ?, ?, ?)",
        ("reep_p1", "player", "Bukayo Saka", "right winger", "England"),
    )
    conn.execute(
        "INSERT INTO squad_membership (reep_id, team_reep_id, season, league) VALUES (?, ?, ?, ?)",
        ("reep_p1", "reep_t1", "2024-2025", "Premier League"),
    )
    conn.execute(
        """INSERT INTO player_season_stats
           (reep_id, season, league, source, minutes_played, goals, assists, xg)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("reep_p1", "2024-2025", "Premier League", "fbref", 2500, 16, 9, 12.3),
    )
    conn.commit()
    client = TestClient(app)
    resp = client.get("/api/team/reep_t1/squad?season=2024-2025")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Bukayo Saka"
    assert data[0]["goals"] == 16
