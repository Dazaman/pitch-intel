from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def test_ingest_people(db):
    from pipeline.stages.identity import ingest_people_csv

    ingest_people_csv(db, FIXTURES / "people_sample.csv")

    rows = db.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    assert rows == 3

    palmer = db.execute(
        "SELECT * FROM people WHERE reep_id = ?", ("reep_p2804f5db",)
    ).fetchone()
    assert palmer["name"] == "Cole Palmer"
    assert palmer["key_fbref"] == "dc7f8a28"
    assert palmer["key_understat"] == "10903"
    assert palmer["position"] == "attacking midfielder"
    assert palmer["height_cm"] == 185


def test_ingest_teams(db):
    from pipeline.stages.identity import ingest_teams_csv

    ingest_teams_csv(db, FIXTURES / "teams_sample.csv")

    rows = db.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    assert rows == 2

    arsenal = db.execute(
        "SELECT * FROM teams WHERE reep_id = ?", ("reep_t0871097b",)
    ).fetchone()
    assert arsenal["name"] == "Arsenal F.C."
    assert arsenal["key_fbref"] == "18bb7c10"
    assert arsenal["key_clubelo"] == "Arsenal"


def test_ingest_people_upsert(db):
    """Running ingest twice should update, not duplicate."""
    from pipeline.stages.identity import ingest_people_csv

    ingest_people_csv(db, FIXTURES / "people_sample.csv")
    ingest_people_csv(db, FIXTURES / "people_sample.csv")

    rows = db.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    assert rows == 3


def test_ingest_filters_players_only(db):
    from pipeline.stages.identity import ingest_people_csv

    ingest_people_csv(db, FIXTURES / "people_sample.csv")

    players = db.execute(
        "SELECT COUNT(*) FROM people WHERE type = 'player'"
    ).fetchone()[0]
    coaches = db.execute(
        "SELECT COUNT(*) FROM people WHERE type = 'coach'"
    ).fetchone()[0]

    assert players == 2
    assert coaches == 1
