import sqlite3
from datetime import datetime

import polars as pl

from pipeline.config import SCHEMA_PATH, TURSO_AUTH_TOKEN, TURSO_DATABASE_URL


def get_connection(local_path: str | None = None) -> sqlite3.Connection:
    """Return a database connection.

    If local_path is given, use a local SQLite file (for tests).
    Otherwise connect to Turso via libsql.
    """
    if local_path:
        return sqlite3.connect(local_path)

    import libsql_experimental as libsql

    conn = libsql.connect(
        "pitch-intel.db",
        sync_url=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN,
    )
    conn.sync()
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes from schema.sql."""
    sql = SCHEMA_PATH.read_text()
    conn.executescript(sql)
    conn.commit()


_PSS_COLUMNS = [
    "reep_id",
    "team_reep_id",
    "season",
    "league",
    "minutes_played",
    "games",
    "starts",
    "goals",
    "shots",
    "shots_on_target",
    "xg",
    "npxg",
    "assists",
    "xa",
    "key_passes",
    "passes_completed",
    "passes_attempted",
    "progressive_passes",
    "progressive_carries",
    "progressive_passes_received",
    "tackles",
    "interceptions",
    "blocks",
    "pressures",
    "pressure_successes",
    "touches",
    "carries",
    "take_ons_attempted",
    "take_ons_succeeded",
    "yellow_cards",
    "red_cards",
    "aerials_won",
    "aerials_lost",
    "source",
]


def upsert_player_stats(conn: sqlite3.Connection, df: pl.DataFrame) -> int:
    """Upsert player season stats from a polars DataFrame. Returns row count."""
    available = [c for c in _PSS_COLUMNS if c in df.columns]
    placeholders = ", ".join("?" for _ in available)
    col_names = ", ".join(available)
    updates = ", ".join(
        f"{c} = excluded.{c}"
        for c in available
        if c not in ("reep_id", "season", "league", "source")
    )

    sql = (
        f"INSERT INTO player_season_stats ({col_names}) VALUES ({placeholders}) "
        f"ON CONFLICT(reep_id, season, league, source) DO UPDATE SET {updates}, "
        f"fetched_at = datetime('now')"
    )

    rows = df.to_dicts()
    for row in rows:
        values = [row.get(c) for c in available]
        conn.execute(sql, values)

    conn.commit()
    return len(rows)


def upsert_team_stats(conn: sqlite3.Connection, df: pl.DataFrame) -> int:
    """Upsert team season stats from a polars DataFrame. Returns row count."""
    available = [c for c in df.columns if c != "id"]
    placeholders = ", ".join("?" for _ in available)
    col_names = ", ".join(available)
    updates = ", ".join(
        f"{c} = excluded.{c}"
        for c in available
        if c not in ("reep_id", "season", "league", "source")
    )

    sql = (
        f"INSERT INTO team_season_stats ({col_names}) VALUES ({placeholders}) "
        f"ON CONFLICT(reep_id, season, league, source) DO UPDATE SET {updates}, "
        f"fetched_at = datetime('now')"
    )

    rows = df.to_dicts()
    for row in rows:
        values = [row.get(c) for c in available]
        conn.execute(sql, values)

    conn.commit()
    return len(rows)


def upsert_player_per90(conn: sqlite3.Connection, df: pl.DataFrame) -> int:
    """Upsert per-90 + percentile data. Returns row count."""
    available = list(df.columns)
    placeholders = ", ".join("?" for _ in available)
    col_names = ", ".join(available)
    updates = ", ".join(
        f"{c} = excluded.{c}" for c in available if c not in ("reep_id", "season", "league")
    )

    sql = (
        f"INSERT INTO player_per90 ({col_names}) VALUES ({placeholders}) "
        f"ON CONFLICT(reep_id, season, league) DO UPDATE SET {updates}, "
        f"computed_at = datetime('now')"
    )

    rows = df.to_dicts()
    for row in rows:
        values = [row.get(c) for c in available]
        conn.execute(sql, values)

    conn.commit()
    return len(rows)


def log_pipeline_run(
    conn: sqlite3.Connection,
    status: str = "running",
    people_count: int | None = None,
    teams_count: int | None = None,
    stats_fetched: int | None = None,
    match_rate: float | None = None,
    error_log: str | None = None,
) -> int:
    """Insert a pipeline run log entry. Returns the run ID."""
    cursor = conn.execute(
        """INSERT INTO pipeline_runs
           (started_at, status, people_count, teams_count, stats_fetched, match_rate, error_log)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.utcnow().isoformat(),
            status,
            people_count,
            teams_count,
            stats_fetched,
            match_rate,
            error_log,
        ),
    )
    conn.commit()
    return cursor.lastrowid
