import sqlite3
from pathlib import Path

import httpx
import polars as pl

from pipeline.config import REEP_BASE_URL

PEOPLE_COLUMNS = {
    "reep_id": "reep_id",
    "type": "type",
    "name": "name",
    "full_name": "full_name",
    "date_of_birth": "date_of_birth",
    "nationality": "nationality",
    "position": "position",
    "height_cm": "height_cm",
    "key_transfermarkt": "key_transfermarkt",
    "key_fbref": "key_fbref",
    "key_understat": "key_understat",
    "key_sofascore": "key_sofascore",
    "key_fotmob": "key_fotmob",
    "key_wikidata": "key_wikidata",
}

TEAMS_COLUMNS = {
    "reep_id": "reep_id",
    "name": "name",
    "country": "country",
    "founded": "founded",
    "stadium": "stadium",
    "key_transfermarkt": "key_transfermarkt",
    "key_fbref": "key_fbref",
    "key_understat": "key_understat",
    "key_sofascore": "key_sofascore",
    "key_clubelo": "key_clubelo",
    "key_wikidata": "key_wikidata",
}


def ingest_people_csv(conn: sqlite3.Connection, csv_path: Path) -> int:
    """Read people.csv and upsert into the people table. Returns row count."""
    df = pl.read_csv(csv_path, infer_schema=False, truncate_ragged_lines=True)

    available = [c for c in PEOPLE_COLUMNS if c in df.columns]
    df = df.select(available)
    df = df.with_columns([pl.col(c).replace("", None) for c in df.columns])

    if "height_cm" in df.columns:
        df = df.with_columns(pl.col("height_cm").cast(pl.Int64, strict=False))

    rows = df.to_dicts()
    available_db_cols = [PEOPLE_COLUMNS[c] for c in available]
    placeholders = ", ".join("?" for _ in available_db_cols)
    col_names = ", ".join(available_db_cols)
    updates = ", ".join(f"{c} = excluded.{c}" for c in available_db_cols if c != "reep_id")

    sql = (
        f"INSERT INTO people ({col_names}) VALUES ({placeholders}) "
        f"ON CONFLICT(reep_id) DO UPDATE SET {updates}, "
        f"updated_at = datetime('now')"
    )

    for row in rows:
        values = tuple(row.get(c) for c in available)
        conn.execute(sql, values)

    conn.commit()
    return len(rows)


def ingest_teams_csv(conn: sqlite3.Connection, csv_path: Path) -> int:
    """Read teams.csv and upsert into the teams table. Returns row count."""
    df = pl.read_csv(csv_path, infer_schema=False)

    available = [c for c in TEAMS_COLUMNS if c in df.columns]
    df = df.select(available)
    df = df.with_columns([pl.col(c).replace("", None) for c in df.columns])

    rows = df.to_dicts()
    available_db_cols = [TEAMS_COLUMNS[c] for c in available]
    placeholders = ", ".join("?" for _ in available_db_cols)
    col_names = ", ".join(available_db_cols)
    updates = ", ".join(f"{c} = excluded.{c}" for c in available_db_cols if c != "reep_id")

    sql = (
        f"INSERT INTO teams ({col_names}) VALUES ({placeholders}) "
        f"ON CONFLICT(reep_id) DO UPDATE SET {updates}, "
        f"updated_at = datetime('now')"
    )

    for row in rows:
        values = tuple(row.get(c) for c in available)
        conn.execute(sql, values)

    conn.commit()
    return len(rows)


def download_reep_csvs(dest_dir: Path) -> tuple[Path, Path]:
    """Download people.csv and teams.csv from Reep GitHub repo."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    files = {}

    for name in ("people.csv", "teams.csv"):
        url = f"{REEP_BASE_URL}/{name}"
        resp = httpx.get(url, follow_redirects=True, timeout=120)
        resp.raise_for_status()
        path = dest_dir / name
        path.write_bytes(resp.content)
        files[name] = path

    return files["people.csv"], files["teams.csv"]
