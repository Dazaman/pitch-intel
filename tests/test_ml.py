import numpy as np
import polars as pl

from pipeline.stages.ml import (
    compute_clusters,
    compute_embeddings,
    compute_team_profiles,
    find_similar_players,
)


def test_compute_embeddings():
    df = pl.DataFrame(
        {
            "reep_id": ["p1", "p2", "p3"],
            "goals_per90": [0.8, 0.2, 0.7],
            "xg_per90": [0.7, 0.3, 0.6],
            "assists_per90": [0.3, 0.5, 0.2],
            "xa_per90": [0.2, 0.4, 0.1],
            "shots_per90": [3.0, 1.5, 2.8],
            "key_passes_per90": [1.0, 2.0, 0.8],
            "progressive_passes_per90": [2.0, 3.0, 1.5],
            "progressive_carries_per90": [1.5, 1.0, 1.8],
            "tackles_per90": [0.5, 2.0, 0.4],
            "interceptions_per90": [0.3, 1.5, 0.2],
            "pressures_per90": [5.0, 8.0, 4.5],
            "take_ons_per90": [2.0, 0.5, 2.5],
        }
    )

    result = compute_embeddings(df)
    assert len(result) == 3
    assert "reep_id" in result.columns
    assert "embedding" in result.columns
    assert isinstance(result["embedding"][0], bytes)
    emb = np.frombuffer(result["embedding"][0], dtype=np.float32)
    assert len(emb) == 12


def test_find_similar_players():
    df = pl.DataFrame(
        {
            "reep_id": ["p1", "p2", "p3", "p4", "p5"],
            "goals_per90": [0.8, 0.1, 0.7, 0.2, 0.3],
            "xg_per90": [0.7, 0.1, 0.6, 0.2, 0.2],
            "assists_per90": [0.3, 0.1, 0.2, 0.5, 0.4],
            "xa_per90": [0.2, 0.1, 0.1, 0.4, 0.3],
            "shots_per90": [3.0, 0.5, 2.8, 1.0, 1.2],
            "key_passes_per90": [1.0, 0.5, 0.8, 2.0, 1.8],
            "progressive_passes_per90": [2.0, 1.0, 1.5, 3.0, 2.5],
            "progressive_carries_per90": [1.5, 0.5, 1.8, 1.0, 0.8],
            "tackles_per90": [0.5, 3.0, 0.4, 2.0, 2.5],
            "interceptions_per90": [0.3, 2.0, 0.2, 1.5, 1.8],
            "pressures_per90": [5.0, 9.0, 4.5, 8.0, 8.5],
            "take_ons_per90": [2.0, 0.3, 2.5, 0.5, 0.4],
        }
    )

    embeddings = compute_embeddings(df)
    similar = find_similar_players(embeddings, "p1", n=3)

    assert len(similar) == 3
    assert similar[0]["reep_id"] == "p3"
    assert 0 < similar[0]["similarity"] <= 1.0


def test_compute_clusters():
    df = pl.DataFrame(
        {
            "reep_id": [f"p{i}" for i in range(20)],
            "goals_per90": [0.8] * 5 + [0.1] * 5 + [0.4] * 5 + [0.2] * 5,
            "xg_per90": [0.7] * 5 + [0.1] * 5 + [0.3] * 5 + [0.2] * 5,
            "assists_per90": [0.2] * 5 + [0.1] * 5 + [0.5] * 5 + [0.3] * 5,
            "xa_per90": [0.1] * 5 + [0.1] * 5 + [0.4] * 5 + [0.2] * 5,
            "shots_per90": [3.0] * 5 + [0.5] * 5 + [2.0] * 5 + [1.0] * 5,
            "key_passes_per90": [1.0] * 5 + [0.5] * 5 + [2.5] * 5 + [1.5] * 5,
            "progressive_passes_per90": [1.5] * 5 + [1.0] * 5 + [3.0] * 5 + [2.0] * 5,
            "progressive_carries_per90": [2.0] * 5 + [0.5] * 5 + [1.0] * 5 + [1.5] * 5,
            "tackles_per90": [0.5] * 5 + [3.0] * 5 + [0.8] * 5 + [2.0] * 5,
            "interceptions_per90": [0.3] * 5 + [2.0] * 5 + [0.5] * 5 + [1.5] * 5,
            "pressures_per90": [5.0] * 5 + [9.0] * 5 + [6.0] * 5 + [8.0] * 5,
            "take_ons_per90": [2.5] * 5 + [0.3] * 5 + [1.5] * 5 + [0.8] * 5,
        }
    )

    embeddings = compute_embeddings(df)
    clustered = compute_clusters(embeddings, n_clusters=4)

    assert "cluster_id" in clustered.columns
    assert "cluster_label" in clustered.columns
    assert "umap_x" in clustered.columns
    assert "umap_y" in clustered.columns
    assert len(clustered) == 20


def test_compute_team_profiles(db):
    db.execute("INSERT INTO teams (reep_id, name) VALUES (?, ?)", ("t1", "Arsenal"))
    db.execute(
        "INSERT INTO people (reep_id, type, name, position, date_of_birth) VALUES (?, ?, ?, ?, ?)",
        ("p1", "player", "Saka", "right winger", "2001-09-05"),
    )
    db.execute(
        "INSERT INTO people (reep_id, type, name, position, date_of_birth) VALUES (?, ?, ?, ?, ?)",
        ("p2", "player", "Rice", "defensive midfield", "1999-01-14"),
    )
    db.execute(
        "INSERT INTO squad_membership (reep_id, team_reep_id, season, league) VALUES (?, ?, ?, ?)",
        ("p1", "t1", "2024-2025", "Premier League"),
    )
    db.execute(
        "INSERT INTO squad_membership (reep_id, team_reep_id, season, league) VALUES (?, ?, ?, ?)",
        ("p2", "t1", "2024-2025", "Premier League"),
    )
    db.execute(
        """INSERT INTO player_season_stats
           (reep_id, season, league, source, minutes_played, goals, assists, xg,
            passes_completed, passes_attempted, progressive_passes, pressures, pressure_successes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "p1",
            "2024-2025",
            "Premier League",
            "understat",
            2500,
            16,
            12,
            13.2,
            1100,
            1380,
            82,
            210,
            68,
        ),
    )
    db.execute(
        """INSERT INTO player_season_stats
           (reep_id, season, league, source, minutes_played, goals, assists, xg,
            passes_completed, passes_attempted, progressive_passes, pressures, pressure_successes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "p2",
            "2024-2025",
            "Premier League",
            "understat",
            2800,
            5,
            7,
            4.2,
            1900,
            2150,
            105,
            265,
            88,
        ),
    )
    db.execute(
        """INSERT INTO team_season_stats
           (reep_id, season, league, source, ppda, xg, xga)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("t1", "2024-2025", "Premier League", "understat", 8.5, 78.5, 33.2),
    )
    db.commit()

    profiles = compute_team_profiles(db, "2024-2025")

    assert len(profiles) == 1
    p = profiles[0]
    assert p["reep_id"] == "t1"
    assert "possession_score" in p
    assert "pressing_score" in p
    assert "avg_age" in p
    assert p["squad_size"] == 2
