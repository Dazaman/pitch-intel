from pipeline.stages.resolve import (
    build_provider_index,
    resolve_clubelo_to_reep,
    resolve_fbref_to_reep,
    resolve_understat_to_reep,
)


def test_build_provider_index(db):
    """Build lookup dicts from the people/teams tables."""
    db.execute(
        "INSERT INTO people (reep_id, type, name, key_fbref, key_understat) VALUES (?, ?, ?, ?, ?)",
        ("reep_p1", "player", "Cole Palmer", "dc7f8a28", "10903"),
    )
    db.execute(
        "INSERT INTO people (reep_id, type, name, key_fbref) VALUES (?, ?, ?, ?)",
        ("reep_p2", "player", "Bukayo Saka", "abc123"),
    )
    db.commit()

    fbref_idx, understat_idx = build_provider_index(db)

    assert fbref_idx["dc7f8a28"] == "reep_p1"
    assert fbref_idx["abc123"] == "reep_p2"
    assert understat_idx["10903"] == "reep_p1"


def test_resolve_fbref_to_reep(db):
    db.execute(
        "INSERT INTO people (reep_id, type, name, key_fbref) VALUES (?, ?, ?, ?)",
        ("reep_p1", "player", "Cole Palmer", "dc7f8a28"),
    )
    db.commit()

    import polars as pl

    stats = pl.DataFrame(
        {
            "player_name": ["Cole Palmer", "Unknown Player"],
            "fbref_id": ["dc7f8a28", "zzz999"],
            "goals": [22, 5],
        }
    )

    resolved, unresolved = resolve_fbref_to_reep(db, stats)

    assert len(resolved) == 1
    assert resolved["reep_id"][0] == "reep_p1"
    assert len(unresolved) == 1
    assert unresolved["player_name"][0] == "Unknown Player"


def test_resolve_understat_to_reep(db):
    db.execute(
        "INSERT INTO people (reep_id, type, name, key_understat) VALUES (?, ?, ?, ?)",
        ("reep_p1", "player", "Cole Palmer", "10903"),
    )
    db.commit()

    import polars as pl

    stats = pl.DataFrame(
        {
            "player_name": ["Cole Palmer"],
            "understat_id": ["10903"],
            "goals": [22],
        }
    )

    resolved, unresolved = resolve_understat_to_reep(db, stats)

    assert len(resolved) == 1
    assert resolved["reep_id"][0] == "reep_p1"
    assert len(unresolved) == 0


def test_resolve_clubelo_to_reep(db):
    db.execute(
        "INSERT INTO teams (reep_id, name, key_clubelo) VALUES (?, ?, ?)",
        ("reep_t1", "Arsenal F.C.", "Arsenal"),
    )
    db.commit()

    import polars as pl

    elo_df = pl.DataFrame(
        {
            "club": ["Arsenal", "Unknown FC"],
            "elo": [2050, 1500],
        }
    )

    resolved, unresolved = resolve_clubelo_to_reep(db, elo_df)

    assert len(resolved) == 1
    assert resolved["reep_id"][0] == "reep_t1"
    assert len(unresolved) == 1
