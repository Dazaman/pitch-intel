import numpy as np
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


def _seed_ml_data(conn):
    conn.execute(
        "INSERT INTO people (reep_id, type, name, position) VALUES (?, ?, ?, ?)",
        ("p1", "player", "Cole Palmer", "attacking midfielder"),
    )
    conn.execute(
        "INSERT INTO people (reep_id, type, name, position) VALUES (?, ?, ?, ?)",
        ("p2", "player", "Bukayo Saka", "right winger"),
    )
    conn.execute("INSERT INTO teams (reep_id, name) VALUES (?, ?)", ("t1", "Arsenal"))

    emb1 = np.array([0.8, 0.7, 0.3, 0.2, 0.9, 0.5, 0.6, 0.7, 0.2, 0.1, 0.3, 0.8], dtype=np.float32)
    emb2 = np.array([0.6, 0.5, 0.4, 0.3, 0.7, 0.6, 0.5, 0.6, 0.3, 0.2, 0.4, 0.7], dtype=np.float32)
    conn.execute(
        """INSERT INTO player_embeddings (reep_id, season, embedding, cluster_id, cluster_label)
           VALUES (?, ?, ?, ?, ?)""",
        ("p1", "2024-2025", emb1.tobytes(), 0, "Goal Scorer"),
    )
    conn.execute(
        """INSERT INTO player_embeddings (reep_id, season, embedding, cluster_id, cluster_label)
           VALUES (?, ?, ?, ?, ?)""",
        ("p2", "2024-2025", emb2.tobytes(), 0, "Goal Scorer"),
    )

    conn.execute(
        """INSERT INTO team_profiles
           (reep_id, season, league, possession_score, pressing_score,
            directness_score, avg_age, squad_size, fw_depth, mf_depth, df_depth, gk_depth)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("t1", "2024-2025", "Premier League", 72.0, 65.0, 45.0, 26.5, 25, 5, 8, 9, 3),
    )
    conn.commit()


def test_similar_players():
    conn = _setup_test_db()
    _seed_ml_data(conn)
    client = TestClient(app)
    resp = client.get("/api/player/p1/similar?n=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["reep_id"] == "p2"
    assert data[0]["similarity"] > 0


def test_team_profile():
    conn = _setup_test_db()
    _seed_ml_data(conn)
    client = TestClient(app)
    resp = client.get("/api/team/t1/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["possession_score"] == 72.0
    assert data["pressing_score"] == 65.0


def test_team_gaps():
    conn = _setup_test_db()
    _seed_ml_data(conn)
    client = TestClient(app)
    resp = client.get("/api/team/t1/gaps")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
    assert any(g["position_group"] == "GK" and g["depth"] == 3 for g in data)


def test_clusters():
    conn = _setup_test_db()
    _seed_ml_data(conn)
    client = TestClient(app)
    resp = client.get("/api/explore/clusters?season=2024-2025")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert "umap_x" in data[0]
    assert "cluster_label" in data[0]
