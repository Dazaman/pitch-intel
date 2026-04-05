import polars as pl

from pipeline.db import (
    log_pipeline_run,
    upsert_player_stats,
)


def test_upsert_player_stats(db):
    db.execute(
        "INSERT INTO people (reep_id, type, name) VALUES (?, ?, ?)",
        ("reep_p1", "player", "Test Player"),
    )
    db.commit()

    df = pl.DataFrame(
        {
            "reep_id": ["reep_p1"],
            "season": ["2024-2025"],
            "league": ["Premier League"],
            "source": ["fbref"],
            "minutes_played": [2700],
            "games": [30],
            "starts": [28],
            "goals": [18],
            "assists": [9],
            "xg": [15.0],
            "npxg": [13.0],
            "xa": [8.0],
            "shots": [80],
            "shots_on_target": [35],
            "key_passes": [50],
            "passes_completed": [1200],
            "passes_attempted": [1500],
            "progressive_passes": [70],
            "progressive_carries": [55],
            "progressive_passes_received": [110],
            "tackles": [20],
            "interceptions": [15],
            "blocks": [10],
            "pressures": [150],
            "pressure_successes": [50],
            "touches": [2200],
            "carries": [1400],
            "take_ons_attempted": [80],
            "take_ons_succeeded": [40],
            "yellow_cards": [3],
            "red_cards": [0],
            "aerials_won": [15],
            "aerials_lost": [10],
        }
    )

    upsert_player_stats(db, df)

    row = db.execute("SELECT * FROM player_season_stats WHERE reep_id = ?", ("reep_p1",)).fetchone()
    assert row is not None
    assert row["goals"] == 18
    assert row["xg"] == 15.0


def test_upsert_player_stats_updates_on_conflict(db):
    db.execute(
        "INSERT INTO people (reep_id, type, name) VALUES (?, ?, ?)",
        ("reep_p1", "player", "Test Player"),
    )
    db.commit()

    df1 = pl.DataFrame(
        {
            "reep_id": ["reep_p1"],
            "season": ["2024-2025"],
            "league": ["Premier League"],
            "source": ["fbref"],
            "goals": [10],
        }
    )
    df2 = pl.DataFrame(
        {
            "reep_id": ["reep_p1"],
            "season": ["2024-2025"],
            "league": ["Premier League"],
            "source": ["fbref"],
            "goals": [18],
        }
    )

    upsert_player_stats(db, df1)
    upsert_player_stats(db, df2)

    count = db.execute("SELECT COUNT(*) FROM player_season_stats").fetchone()[0]
    assert count == 1

    row = db.execute(
        "SELECT goals FROM player_season_stats WHERE reep_id = ?", ("reep_p1",)
    ).fetchone()
    assert row[0] == 18


def test_log_pipeline_run(db):
    run_id = log_pipeline_run(db, status="running")
    assert run_id is not None

    row = db.execute("SELECT * FROM pipeline_runs WHERE id = ?", (run_id,)).fetchone()
    assert row["status"] == "running"
