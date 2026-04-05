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


def test_search_players():
    conn = _setup_test_db()
    conn.execute(
        "INSERT INTO people (reep_id, type, name, nationality, position) VALUES (?, ?, ?, ?, ?)",
        ("reep_p1", "player", "Cole Palmer", "United Kingdom", "attacking midfielder"),
    )
    conn.execute(
        "INSERT INTO people (reep_id, type, name, nationality, position) VALUES (?, ?, ?, ?, ?)",
        ("reep_p2", "player", "Bukayo Saka", "United Kingdom", "right winger"),
    )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/search?q=Palmer&type=player")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Cole Palmer"


def test_search_teams():
    conn = _setup_test_db()
    conn.execute(
        "INSERT INTO teams (reep_id, name, country) VALUES (?, ?, ?)",
        ("reep_t1", "Arsenal F.C.", "United Kingdom"),
    )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/search?q=Arsenal&type=team")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Arsenal F.C."


def test_search_all_types():
    conn = _setup_test_db()
    conn.execute(
        "INSERT INTO people (reep_id, type, name) VALUES (?, ?, ?)",
        ("reep_p1", "player", "Martin Arsenal"),
    )
    conn.execute(
        "INSERT INTO teams (reep_id, name) VALUES (?, ?)",
        ("reep_t1", "Arsenal F.C."),
    )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/search?q=Arsenal")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2


def test_search_min_length():
    _setup_test_db()
    client = TestClient(app)
    resp = client.get("/api/search?q=a")
    assert resp.status_code == 422
