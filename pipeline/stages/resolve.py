import sqlite3

import polars as pl


def build_provider_index(conn: sqlite3.Connection) -> tuple[dict, dict]:
    """Build lookup dicts: provider_id -> reep_id.

    Returns (fbref_index, understat_index).
    """
    fbref_idx = {}
    understat_idx = {}

    rows = conn.execute("SELECT reep_id, key_fbref, key_understat FROM people").fetchall()

    for row in rows:
        reep_id = row[0]
        if row[1]:
            fbref_idx[row[1]] = reep_id
        if row[2]:
            understat_idx[row[2]] = reep_id

    return fbref_idx, understat_idx


def _build_teams_clubelo_index(conn: sqlite3.Connection) -> dict:
    """Build lookup: clubelo_name -> reep_id."""
    rows = conn.execute(
        "SELECT reep_id, key_clubelo FROM teams WHERE key_clubelo IS NOT NULL"
    ).fetchall()
    return {row[1]: row[0] for row in rows}


def resolve_fbref_to_reep(
    conn: sqlite3.Connection,
    stats_df: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Resolve FBref player stats to reep_ids.

    Returns (resolved_df with reep_id column, unresolved_df).
    """
    fbref_idx, _ = build_provider_index(conn)

    reep_ids = [fbref_idx.get(fid) for fid in stats_df["fbref_id"].to_list()]

    df = stats_df.with_columns(pl.Series("reep_id", reep_ids))
    resolved = df.filter(pl.col("reep_id").is_not_null())
    unresolved = df.filter(pl.col("reep_id").is_null()).drop("reep_id")

    return resolved, unresolved


def resolve_understat_to_reep(
    conn: sqlite3.Connection,
    stats_df: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Resolve Understat player stats to reep_ids.

    Returns (resolved_df with reep_id column, unresolved_df).
    """
    _, understat_idx = build_provider_index(conn)

    reep_ids = [understat_idx.get(uid) for uid in stats_df["understat_id"].to_list()]

    df = stats_df.with_columns(pl.Series("reep_id", reep_ids))
    resolved = df.filter(pl.col("reep_id").is_not_null())
    unresolved = df.filter(pl.col("reep_id").is_null()).drop("reep_id")

    return resolved, unresolved


def build_team_understat_index(conn: sqlite3.Connection) -> dict:
    """Build lookup: understat_team_id (str) -> reep_id."""
    rows = conn.execute(
        "SELECT reep_id, key_understat FROM teams WHERE key_understat IS NOT NULL"
    ).fetchall()
    return {row[1]: row[0] for row in rows}


def resolve_understat_teams(
    conn: sqlite3.Connection,
    stats_df: pl.DataFrame,
) -> pl.DataFrame:
    """Add team_reep_id to a DataFrame that has a team_id column (Understat team ID).

    Also populates squad_membership for resolved player-team pairs.
    Returns the DataFrame with team_reep_id added.
    """
    team_idx = build_team_understat_index(conn)

    # The normalized Understat DataFrame may have team_name but not team_id
    # We need the original team_id from soccerdata. If present, use it directly.
    if "team_id" in stats_df.columns:
        team_reep_ids = [team_idx.get(str(tid)) for tid in stats_df["team_id"].to_list()]
    else:
        team_reep_ids = [None] * len(stats_df)

    return stats_df.with_columns(pl.Series("team_reep_id", team_reep_ids))


def resolve_clubelo_to_reep(
    conn: sqlite3.Connection,
    elo_df: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Resolve ClubElo team names to reep_ids.

    Returns (resolved_df with reep_id column, unresolved_df).
    """
    clubelo_idx = _build_teams_clubelo_index(conn)

    reep_ids = [clubelo_idx.get(name) for name in elo_df["club"].to_list()]

    df = elo_df.with_columns(pl.Series("reep_id", reep_ids))
    resolved = df.filter(pl.col("reep_id").is_not_null())
    unresolved = df.filter(pl.col("reep_id").is_null()).drop("reep_id")

    return resolved, unresolved
