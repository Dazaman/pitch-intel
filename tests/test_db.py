def test_schema_creates_all_tables(db):
    cursor = db.execute(
        "SELECT name FROM sqlite_master"
        " WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]

    expected = [
        "people",
        "pipeline_runs",
        "player_embeddings",
        "player_per90",
        "player_season_stats",
        "shots",
        "squad_membership",
        "team_profiles",
        "team_season_stats",
        "teams",
    ]
    assert tables == expected


def test_schema_creates_indexes(db):
    cursor = db.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name"
    )
    indexes = [row[0] for row in cursor.fetchall()]

    assert "idx_people_fbref" in indexes
    assert "idx_people_understat" in indexes
    assert "idx_teams_fbref" in indexes
    assert "idx_shots_reep" in indexes
    assert "idx_squad_team" in indexes


def test_people_insert_and_query(db):
    db.execute(
        "INSERT INTO people (reep_id, type, name, key_fbref) VALUES (?, ?, ?, ?)",
        ("reep_p2804f5db", "player", "Cole Palmer", "dc7f8a28"),
    )
    db.commit()

    row = db.execute("SELECT * FROM people WHERE key_fbref = ?", ("dc7f8a28",)).fetchone()

    assert row["reep_id"] == "reep_p2804f5db"
    assert row["name"] == "Cole Palmer"


def test_unique_constraint_on_player_season_stats(db):
    import sqlite3 as _sqlite3

    import pytest

    db.execute(
        "INSERT INTO people (reep_id, type, name) VALUES (?, ?, ?)",
        ("reep_p1", "player", "Test Player"),
    )
    db.execute(
        """INSERT INTO player_season_stats
           (reep_id, season, league, source, goals)
           VALUES (?, ?, ?, ?, ?)""",
        ("reep_p1", "2024-2025", "Premier League", "fbref", 10),
    )
    db.commit()

    with pytest.raises(_sqlite3.IntegrityError):
        db.execute(
            """INSERT INTO player_season_stats
               (reep_id, season, league, source, goals)
               VALUES (?, ?, ?, ?, ?)""",
            ("reep_p1", "2024-2025", "Premier League", "fbref", 12),
        )
