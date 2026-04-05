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


def test_health_no_pipeline_runs():
    _setup_test_db()
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "no_pipeline_runs"
    assert data["people_count"] == 0


def test_health_with_pipeline_run():
    conn = _setup_test_db()
    conn.execute(
        """INSERT INTO pipeline_runs (started_at, status, people_count, teams_count)
           VALUES (?, ?, ?, ?)""",
        ("2026-04-06T10:00:00", "completed", 488000, 45000),
    )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["people_count"] == 488000
