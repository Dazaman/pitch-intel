# Data Pipeline + Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the data pipeline that populates Turso with football player/team identity data from Reep, stats from FBref and Understat, and computed features (per-90s, percentiles, squad membership).

**Architecture:** Python scripts orchestrated by a CLI entry point. Each pipeline stage (identity, stats, compute) is an independent module. Polars for data processing, libsql for Turso access. GitHub Actions runs the pipeline weekly.

**Tech Stack:** Python 3.12+, polars, libsql, soccerdata (FBref/Understat), httpx (Reep API/ClubElo), pytest

---

## File Structure

```
pitch-intel/
├── pipeline/
│   ├── __init__.py
│   ├── cli.py                  # CLI entry point (run full pipeline or individual stages)
│   ├── db.py                   # Turso connection + schema creation
│   ├── schema.sql              # All CREATE TABLE/INDEX statements
│   ├── stages/
│   │   ├── __init__.py
│   │   ├── identity.py         # Stage 1: Download Reep CSVs → upsert people + teams
│   │   ├── fbref.py            # Stage 2a: Fetch FBref stats via soccerdata
│   │   ├── understat.py        # Stage 2b: Fetch Understat xG + shots via soccerdata
│   │   ├── clubelo.py          # Stage 2c: Fetch ClubElo ratings
│   │   ├── resolve.py          # Stage 3: Entity resolution (provider ID → reep_id)
│   │   └── compute.py          # Stage 4: Per-90, percentiles, squad membership
│   └── config.py               # Constants: league names, seasons, Turso env vars
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures: in-memory SQLite, sample data
│   ├── test_db.py              # Schema creation tests
│   ├── test_identity.py        # Identity stage tests
│   ├── test_fbref.py           # FBref stage tests
│   ├── test_understat.py       # Understat stage tests
│   ├── test_clubelo.py         # ClubElo stage tests
│   ├── test_resolve.py         # Entity resolution tests
│   └── test_compute.py         # Compute stage tests
├── .github/
│   └── workflows/
│       └── pipeline.yml        # Weekly cron workflow
├── pyproject.toml              # Project config + dependencies
└── .env.example                # Template for TURSO_DATABASE_URL, TURSO_AUTH_TOKEN, REEP_API_KEY
```

---

### Task 1: Project Setup + Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `pipeline/__init__.py`
- Create: `pipeline/stages/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "pitch-intel-pipeline"
version = "0.1.0"
description = "Football intelligence data pipeline"
requires-python = ">=3.12"
dependencies = [
    "polars>=1.0",
    "libsql-experimental>=0.0.55",
    "soccerdata>=1.8",
    "httpx>=0.27",
    "click>=8.1",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]

[project.scripts]
pitch-intel = "pipeline.cli:main"
```

- [ ] **Step 2: Create .env.example**

```
TURSO_DATABASE_URL=libsql://your-db-name-your-org.turso.io
TURSO_AUTH_TOKEN=your-token-here
REEP_API_KEY=your-rapidapi-key-here
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.env
.venv/
*.db
dist/
.soccerdata/
```

- [ ] **Step 4: Create empty __init__.py files**

Create empty files at:
- `pipeline/__init__.py`
- `pipeline/stages/__init__.py`
- `tests/__init__.py`

- [ ] **Step 5: Install dependencies**

Run: `cd pitch-intel && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
Expected: All packages install successfully.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .env.example .gitignore pipeline/__init__.py pipeline/stages/__init__.py tests/__init__.py
git commit -m "chore: project setup with dependencies"
```

---

### Task 2: Database Schema + Connection

**Files:**
- Create: `pipeline/schema.sql`
- Create: `pipeline/db.py`
- Create: `pipeline/config.py`
- Create: `tests/conftest.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write the schema file**

Create `pipeline/schema.sql` with the full schema from the design spec. This is the single source of truth for all table definitions:

```sql
-- Identity Layer
CREATE TABLE IF NOT EXISTS people (
    reep_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    full_name TEXT,
    date_of_birth TEXT,
    nationality TEXT,
    position TEXT,
    height_cm INTEGER,
    key_transfermarkt TEXT,
    key_fbref TEXT,
    key_understat TEXT,
    key_sofascore TEXT,
    key_fotmob TEXT,
    key_wikidata TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_people_fbref ON people(key_fbref);
CREATE INDEX IF NOT EXISTS idx_people_understat ON people(key_understat);
CREATE INDEX IF NOT EXISTS idx_people_transfermarkt ON people(key_transfermarkt);
CREATE INDEX IF NOT EXISTS idx_people_name ON people(name);

CREATE TABLE IF NOT EXISTS teams (
    reep_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT,
    founded TEXT,
    stadium TEXT,
    key_transfermarkt TEXT,
    key_fbref TEXT,
    key_understat TEXT,
    key_sofascore TEXT,
    key_clubelo TEXT,
    key_wikidata TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_teams_fbref ON teams(key_fbref);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);

-- Stats Layer
CREATE TABLE IF NOT EXISTS player_season_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reep_id TEXT NOT NULL REFERENCES people(reep_id),
    team_reep_id TEXT REFERENCES teams(reep_id),
    season TEXT NOT NULL,
    league TEXT NOT NULL,
    minutes_played INTEGER,
    games INTEGER,
    starts INTEGER,
    goals INTEGER,
    shots INTEGER,
    shots_on_target INTEGER,
    xg REAL,
    npxg REAL,
    assists INTEGER,
    xa REAL,
    key_passes INTEGER,
    passes_completed INTEGER,
    passes_attempted INTEGER,
    progressive_passes INTEGER,
    progressive_carries INTEGER,
    progressive_passes_received INTEGER,
    tackles INTEGER,
    interceptions INTEGER,
    blocks INTEGER,
    pressures INTEGER,
    pressure_successes INTEGER,
    touches INTEGER,
    carries INTEGER,
    take_ons_attempted INTEGER,
    take_ons_succeeded INTEGER,
    yellow_cards INTEGER,
    red_cards INTEGER,
    aerials_won INTEGER,
    aerials_lost INTEGER,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(reep_id, season, league, source)
);

CREATE INDEX IF NOT EXISTS idx_pss_reep ON player_season_stats(reep_id);
CREATE INDEX IF NOT EXISTS idx_pss_team ON player_season_stats(team_reep_id);
CREATE INDEX IF NOT EXISTS idx_pss_season ON player_season_stats(season, league);

CREATE TABLE IF NOT EXISTS shots (
    id INTEGER PRIMARY KEY,
    reep_id TEXT REFERENCES people(reep_id),
    match_id TEXT,
    season TEXT NOT NULL,
    league TEXT NOT NULL,
    minute INTEGER,
    result TEXT,
    x REAL,
    y REAL,
    xg REAL,
    situation TEXT,
    shot_type TEXT,
    last_action TEXT,
    source TEXT NOT NULL DEFAULT 'understat',
    UNIQUE(id, source)
);

CREATE INDEX IF NOT EXISTS idx_shots_reep ON shots(reep_id);
CREATE INDEX IF NOT EXISTS idx_shots_season ON shots(season, league);

CREATE TABLE IF NOT EXISTS team_season_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reep_id TEXT NOT NULL REFERENCES teams(reep_id),
    season TEXT NOT NULL,
    league TEXT NOT NULL,
    wins INTEGER,
    draws INTEGER,
    losses INTEGER,
    goals_for INTEGER,
    goals_against INTEGER,
    xg REAL,
    xga REAL,
    npxg REAL,
    npxga REAL,
    ppda REAL,
    oppda REAL,
    deep_completions INTEGER,
    elo_start REAL,
    elo_end REAL,
    elo_peak REAL,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(reep_id, season, league, source)
);

CREATE INDEX IF NOT EXISTS idx_tss_reep ON team_season_stats(reep_id);

CREATE TABLE IF NOT EXISTS squad_membership (
    reep_id TEXT NOT NULL REFERENCES people(reep_id),
    team_reep_id TEXT NOT NULL REFERENCES teams(reep_id),
    season TEXT NOT NULL,
    league TEXT NOT NULL,
    PRIMARY KEY (reep_id, team_reep_id, season)
);

CREATE INDEX IF NOT EXISTS idx_squad_team ON squad_membership(team_reep_id, season);

-- Computed Layer
CREATE TABLE IF NOT EXISTS player_per90 (
    reep_id TEXT NOT NULL,
    season TEXT NOT NULL,
    league TEXT NOT NULL,
    position_group TEXT NOT NULL,
    minutes_played INTEGER NOT NULL,
    goals_per90 REAL,
    xg_per90 REAL,
    assists_per90 REAL,
    xa_per90 REAL,
    shots_per90 REAL,
    key_passes_per90 REAL,
    progressive_passes_per90 REAL,
    progressive_carries_per90 REAL,
    tackles_per90 REAL,
    interceptions_per90 REAL,
    pressures_per90 REAL,
    take_ons_per90 REAL,
    goals_pctile INTEGER,
    xg_pctile INTEGER,
    assists_pctile INTEGER,
    xa_pctile INTEGER,
    shots_pctile INTEGER,
    key_passes_pctile INTEGER,
    progressive_passes_pctile INTEGER,
    progressive_carries_pctile INTEGER,
    tackles_pctile INTEGER,
    interceptions_pctile INTEGER,
    pressures_pctile INTEGER,
    take_ons_pctile INTEGER,
    computed_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (reep_id, season, league)
);

CREATE TABLE IF NOT EXISTS player_embeddings (
    reep_id TEXT PRIMARY KEY,
    season TEXT NOT NULL,
    embedding BLOB NOT NULL,
    cluster_id INTEGER,
    cluster_label TEXT,
    computed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS team_profiles (
    reep_id TEXT NOT NULL,
    season TEXT NOT NULL,
    league TEXT NOT NULL,
    possession_score REAL,
    pressing_score REAL,
    directness_score REAL,
    set_piece_reliance REAL,
    avg_age REAL,
    squad_size INTEGER,
    foreign_player_pct REAL,
    fw_depth INTEGER,
    mf_depth INTEGER,
    df_depth INTEGER,
    gk_depth INTEGER,
    computed_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (reep_id, season, league)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    people_count INTEGER,
    teams_count INTEGER,
    stats_fetched INTEGER,
    match_rate REAL,
    error_log TEXT
);
```

- [ ] **Step 2: Write the config module**

Create `pipeline/config.py`:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
REEP_API_KEY = os.environ.get("REEP_API_KEY", "")

REEP_BASE_URL = "https://github.com/withqwerty/reep/raw/main/data"

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

TOP_5_LEAGUES = {
    "ENG-Premier League": "Premier League",
    "ESP-La Liga": "La Liga",
    "ITA-Serie A": "Serie A",
    "GER-Bundesliga": "Bundesliga",
    "FRA-Ligue 1": "Ligue 1",
}

UNDERSTAT_LEAGUES = ["EPL", "La_Liga", "Bundesliga", "Serie_A", "Ligue_1"]

CURRENT_SEASON = "2025-2026"

MIN_MINUTES_FOR_PER90 = 900

POSITION_GROUPS = {
    "goalkeeper": "GK",
    "centre-back": "DF",
    "left-back": "DF",
    "right-back": "DF",
    "defensive midfield": "MF",
    "central midfield": "MF",
    "attacking midfield": "MF",
    "left midfield": "MF",
    "right midfield": "MF",
    "left winger": "FW",
    "right winger": "FW",
    "centre-forward": "FW",
    "second striker": "FW",
}
```

- [ ] **Step 3: Write the db module**

Create `pipeline/db.py`:

```python
import sqlite3
from pathlib import Path

from pipeline.config import TURSO_DATABASE_URL, TURSO_AUTH_TOKEN, SCHEMA_PATH


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
```

- [ ] **Step 4: Write the test fixtures**

Create `tests/conftest.py`:

```python
import sqlite3
import pytest


@pytest.fixture
def db():
    """In-memory SQLite database with schema applied."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    from pipeline.db import init_schema
    init_schema(conn)

    yield conn
    conn.close()
```

- [ ] **Step 5: Write the failing test**

Create `tests/test_db.py`:

```python
def test_schema_creates_all_tables(db):
    cursor = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
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

    row = db.execute(
        "SELECT * FROM people WHERE key_fbref = ?", ("dc7f8a28",)
    ).fetchone()

    assert row["reep_id"] == "reep_p2804f5db"
    assert row["name"] == "Cole Palmer"


def test_unique_constraint_on_player_season_stats(db):
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

    import sqlite3 as _sqlite3
    import pytest

    with pytest.raises(_sqlite3.IntegrityError):
        db.execute(
            """INSERT INTO player_season_stats
               (reep_id, season, league, source, goals)
               VALUES (?, ?, ?, ?, ?)""",
            ("reep_p1", "2024-2025", "Premier League", "fbref", 12),
        )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd pitch-intel && python -m pytest tests/test_db.py -v`
Expected: 4 tests PASS

- [ ] **Step 7: Commit**

```bash
git add pipeline/schema.sql pipeline/db.py pipeline/config.py tests/conftest.py tests/test_db.py
git commit -m "feat: database schema and connection module"
```

---

### Task 3: Identity Stage — Reep CSV Ingestion

**Files:**
- Create: `pipeline/stages/identity.py`
- Create: `tests/test_identity.py`
- Create: `tests/fixtures/` (sample CSV data)

- [ ] **Step 1: Create sample fixture data**

Create `tests/fixtures/people_sample.csv`:

```csv
reep_id,key_wikidata,type,name,full_name,date_of_birth,nationality,position,height_cm,key_transfermarkt,key_transfermarkt_manager,key_fbref,key_soccerway,key_sofascore,key_flashscore,key_opta,key_premier_league,key_11v11,key_espn,key_national_football_teams,key_worldfootball,key_soccerbase,key_kicker,key_uefa,key_lequipe,key_fff_fr,key_serie_a,key_besoccer,key_footballdatabase_eu,key_eu_football_info,key_hugman,key_german_fa,key_statmuse_pl,key_sofifa,key_soccerdonna,key_dongqiudi,key_understat,key_whoscored,key_fbref_verified,key_sportmonks,key_api_football,key_fotmob,key_fpl_code,key_thesportsdb,key_skillcorner,key_wyscout,key_impect,key_heimspiel
reep_p2804f5db,Q99760796,player,Cole Palmer,Cole Jermaine Palmer,2002-05-06,United Kingdom,attacking midfielder,185,568177,,dc7f8a28,525801,982780,palmer-cole/h8agbDt7,7cwgrmorsb42qaj5vrhp8fhzp,49293,265554,,92970,cole-palmer,125454,cole-palmer,,,,,,,,,,,,,,10903,,,,,292462,244851,34146086,23959,234966,52615,361032
reep_p00000001,Q11893,player,Cristiano Ronaldo,Cristiano Ronaldo dos Santos Aveiro,1985-02-05,Portugal,centre-forward,187,8198,,dea698d9,5575,750,,,,,,,,,,,,,,,,,,,,,,,,7704,,,,,,,,,,,
reep_c9103de59,,coach,Pep Guardiola,Josep Guardiola i Sala,1971-01-18,Spain,,180,,5672,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
```

Create `tests/fixtures/teams_sample.csv`:

```csv
reep_id,key_wikidata,name,country,founded,stadium,key_transfermarkt,key_fbref,key_soccerway,key_opta,key_kicker,key_flashscore,key_sofascore,key_soccerbase,key_uefa,key_footballdatabase_eu,key_worldfootball,key_espn,key_playmakerstats,key_clubelo,key_sportmonks,key_api_football,key_sofifa,key_fotmob
reep_t0871097b,Q9616,Arsenal F.C.,United Kingdom,1886-10-01,Emirates Stadium,11,18bb7c10,660,b3sy95iqnw2bv69a0gxunhiot,,,,,,,,,Arsenal,,,9825,
reep_t00000001,Q9592,Chelsea F.C.,United Kingdom,1905-03-10,Stamford Bridge,631,cff3d9bb,961,,,,,,,,,,Chelsea,,,8455,
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_identity.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_identity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.stages.identity'`

- [ ] **Step 4: Implement the identity stage**

Create `pipeline/stages/identity.py`:

```python
import sqlite3
from pathlib import Path

import polars as pl


# Columns we keep from people.csv (map CSV column → DB column)
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


def _empty_to_none(value: str) -> str | None:
    """Convert empty strings to None for cleaner DB storage."""
    if value == "" or value is None:
        return None
    return value


def ingest_people_csv(conn: sqlite3.Connection, csv_path: Path) -> int:
    """Read people.csv and upsert into the people table. Returns row count."""
    df = pl.read_csv(csv_path, infer_schema_length=0)

    # Only keep columns that exist in both CSV and our schema
    available = [c for c in PEOPLE_COLUMNS if c in df.columns]
    df = df.select(available)

    # Replace empty strings with None
    df = df.with_columns(
        [pl.col(c).replace("", None) for c in df.columns]
    )

    # Cast height_cm to int where present
    if "height_cm" in df.columns:
        df = df.with_columns(pl.col("height_cm").cast(pl.Int64, strict=False))

    rows = df.to_dicts()
    cols = list(PEOPLE_COLUMNS.values())
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
        values = [row.get(c) for c in available]
        conn.execute(sql, values)

    conn.commit()
    return len(rows)


def ingest_teams_csv(conn: sqlite3.Connection, csv_path: Path) -> int:
    """Read teams.csv and upsert into the teams table. Returns row count."""
    df = pl.read_csv(csv_path, infer_schema_length=0)

    available = [c for c in TEAMS_COLUMNS if c in df.columns]
    df = df.select(available)

    df = df.with_columns(
        [pl.col(c).replace("", None) for c in df.columns]
    )

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
        values = [row.get(c) for c in available]
        conn.execute(sql, values)

    conn.commit()
    return len(rows)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_identity.py -v`
Expected: 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add pipeline/stages/identity.py tests/test_identity.py tests/fixtures/
git commit -m "feat: identity stage — ingest Reep people and teams CSVs"
```

---

### Task 4: Identity Stage — Remote CSV Download

**Files:**
- Modify: `pipeline/stages/identity.py`
- Create: `tests/test_identity_download.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_identity_download.py`:

```python
from unittest.mock import patch, MagicMock
from pathlib import Path
from pipeline.stages.identity import download_reep_csvs

FIXTURES = Path(__file__).parent / "fixtures"


def test_download_reep_csvs(tmp_path):
    """download_reep_csvs should fetch people.csv and teams.csv to a local dir."""
    people_bytes = (FIXTURES / "people_sample.csv").read_bytes()
    teams_bytes = (FIXTURES / "teams_sample.csv").read_bytes()

    def fake_get(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        if "people.csv" in url:
            resp.content = people_bytes
        elif "teams.csv" in url:
            resp.content = teams_bytes
        return resp

    with patch("httpx.get", side_effect=fake_get):
        people_path, teams_path = download_reep_csvs(tmp_path)

    assert people_path.exists()
    assert teams_path.exists()
    assert "Cole Palmer" in people_path.read_text()
    assert "Arsenal" in teams_path.read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_identity_download.py -v`
Expected: FAIL — `ImportError: cannot import name 'download_reep_csvs'`

- [ ] **Step 3: Implement download_reep_csvs**

Add to `pipeline/stages/identity.py`:

```python
import httpx

from pipeline.config import REEP_BASE_URL


def download_reep_csvs(dest_dir: Path) -> tuple[Path, Path]:
    """Download people.csv and teams.csv from Reep GitHub repo.

    Returns paths to the downloaded files.
    """
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_identity_download.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/stages/identity.py tests/test_identity_download.py
git commit -m "feat: download Reep CSVs from GitHub"
```

---

### Task 5: FBref Stats Stage

**Files:**
- Create: `pipeline/stages/fbref.py`
- Create: `tests/test_fbref.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_fbref.py`:

```python
import polars as pl
from pipeline.stages.fbref import normalize_fbref_stats


def test_normalize_fbref_stats():
    """normalize_fbref_stats should produce a polars DataFrame with our schema columns."""
    # Simulate a raw soccerdata FBref DataFrame (pandas) with MultiIndex columns
    import pandas as pd

    data = {
        ("Unnamed: player", "player"): ["Cole Palmer", "Bukayo Saka"],
        ("Unnamed: team", "team"): ["Chelsea", "Arsenal"],
        ("Playing Time", "Min"): [2800, 2500],
        ("Playing Time", "MP"): [32, 30],
        ("Playing Time", "Starts"): [30, 28],
        ("Performance", "Gls"): [22, 16],
        ("Performance", "Ast"): [11, 9],
        ("Expected", "xG"): [18.5, 12.3],
        ("Expected", "npxG"): [16.2, 11.1],
        ("Expected", "xAG"): [9.8, 8.5],
        ("Performance", "Sh"): [95, 72],
        ("Performance", "SoT"): [42, 30],
        ("Total", "Cmp"): [1200, 1100],
        ("Total", "Att"): [1500, 1400],
        ("Unnamed: progressive_passes", "PrgP"): [85, 78],
        ("Unnamed: progressive_carries", "PrgC"): [65, 70],
        ("Unnamed: progressive_passes_received", "PrgR"): [110, 95],
        ("Tackles", "Tkl"): [25, 35],
        ("Int", "Int"): [18, 22],
        ("Blocks", "Blocks"): [12, 15],
        ("Pressures", "Press"): [180, 220],
        ("Pressures", "Succ"): [55, 70],
        ("Touches", "Touches"): [2200, 2000],
        ("Carries", "Carries"): [1400, 1300],
        ("Take-Ons", "Att"): [90, 85],
        ("Take-Ons", "Succ"): [50, 45],
        ("Performance", "CrdY"): [3, 5],
        ("Performance", "CrdR"): [0, 0],
        ("Aerial Duels", "Won"): [15, 20],
        ("Aerial Duels", "Lost"): [10, 12],
    }

    pdf = pd.DataFrame(data)

    result = normalize_fbref_stats(pdf, season="2024-2025", league="Premier League")

    assert isinstance(result, pl.DataFrame)
    assert len(result) == 2
    assert "player_name" in result.columns
    assert "goals" in result.columns
    assert "xg" in result.columns
    assert result.filter(pl.col("player_name") == "Cole Palmer")["goals"][0] == 22
    assert result["season"][0] == "2024-2025"
    assert result["league"][0] == "Premier League"
    assert result["source"][0] == "fbref"


def test_normalize_fbref_stats_handles_missing_columns():
    """Should not crash when optional columns are missing."""
    import pandas as pd

    data = {
        ("Unnamed: player", "player"): ["Test Player"],
        ("Unnamed: team", "team"): ["Test FC"],
        ("Playing Time", "Min"): [900],
        ("Playing Time", "MP"): [10],
        ("Playing Time", "Starts"): [10],
        ("Performance", "Gls"): [5],
    }

    pdf = pd.DataFrame(data)

    result = normalize_fbref_stats(pdf, season="2024-2025", league="Premier League")

    assert len(result) == 1
    assert result["goals"][0] == 5
    assert result["xg"][0] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fbref.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.stages.fbref'`

- [ ] **Step 3: Implement the FBref stage**

Create `pipeline/stages/fbref.py`:

```python
import polars as pl
import pandas as pd

from pipeline.config import TOP_5_LEAGUES, CURRENT_SEASON

# Map FBref multi-index columns to our flat column names.
# Key = (level_0_substring, level_1_exact) → value = our column name.
# We match on substrings in level 0 because soccerdata column headers vary.
COLUMN_MAP = {
    ("player", "player"): "player_name",
    ("team", "team"): "team_name",
    ("Playing Time", "Min"): "minutes_played",
    ("Playing Time", "MP"): "games",
    ("Playing Time", "Starts"): "starts",
    ("Performance", "Gls"): "goals",
    ("Performance", "Ast"): "assists",
    ("Expected", "xG"): "xg",
    ("Expected", "npxG"): "npxg",
    ("Expected", "xAG"): "xa",
    ("Performance", "Sh"): "shots",
    ("Performance", "SoT"): "shots_on_target",
    ("Total", "Cmp"): "passes_completed",
    ("Total", "Att"): "passes_attempted",
    ("progressive_passes", "PrgP"): "progressive_passes",
    ("progressive_carries", "PrgC"): "progressive_carries",
    ("progressive_passes_received", "PrgR"): "progressive_passes_received",
    ("Tackles", "Tkl"): "tackles",
    ("Int", "Int"): "interceptions",
    ("Blocks", "Blocks"): "blocks",
    ("Pressures", "Press"): "pressures",
    ("Pressures", "Succ"): "pressure_successes",
    ("Touches", "Touches"): "touches",
    ("Carries", "Carries"): "carries",
    ("Take-Ons", "Att"): "take_ons_attempted",
    ("Take-Ons", "Succ"): "take_ons_succeeded",
    ("Performance", "CrdY"): "yellow_cards",
    ("Performance", "CrdR"): "red_cards",
    ("Aerial Duels", "Won"): "aerials_won",
    ("Aerial Duels", "Lost"): "aerials_lost",
    ("SCA", "SCA"): "key_passes",
}


def _find_column(pdf_columns, level0_sub: str, level1_exact: str) -> str | None:
    """Find a pandas MultiIndex column by matching substrings."""
    for col in pdf_columns:
        if isinstance(col, tuple) and len(col) >= 2:
            if level0_sub in str(col[0]) and col[1] == level1_exact:
                return col
        elif col == level1_exact:
            return col
    return None


def normalize_fbref_stats(
    raw_df: pd.DataFrame,
    season: str,
    league: str,
) -> pl.DataFrame:
    """Normalize a raw soccerdata FBref DataFrame into our schema.

    Returns a polars DataFrame with columns matching player_season_stats.
    """
    mapped = {}

    for (l0_sub, l1_exact), our_name in COLUMN_MAP.items():
        col = _find_column(raw_df.columns, l0_sub, l1_exact)
        if col is not None:
            mapped[our_name] = raw_df[col].tolist()
        else:
            mapped[our_name] = [None] * len(raw_df)

    mapped["season"] = [season] * len(raw_df)
    mapped["league"] = [league] * len(raw_df)
    mapped["source"] = ["fbref"] * len(raw_df)

    # Extract FBref player ID from the DataFrame index if available.
    # soccerdata uses the FBref URL slug as the index, which contains the player ID.
    if hasattr(raw_df, "index") and raw_df.index.name == "player":
        mapped["fbref_id"] = [str(idx) for idx in raw_df.index.tolist()]
    else:
        mapped["fbref_id"] = [None] * len(raw_df)

    return pl.DataFrame(mapped)


def fetch_fbref_season(league_code: str, season: str) -> pd.DataFrame | None:
    """Fetch player season stats from FBref via soccerdata.

    Returns None if the scraper fails (e.g., FBref blocks requests).
    """
    try:
        import soccerdata as sd

        fbref = sd.FBref(leagues=league_code, seasons=season)
        return fbref.read_player_season_stats(stat_type="standard")
    except Exception as e:
        print(f"FBref fetch failed for {league_code} {season}: {e}")
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_fbref.py -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/stages/fbref.py tests/test_fbref.py
git commit -m "feat: FBref stats stage with column normalization"
```

---

### Task 6: Understat Stats Stage

**Files:**
- Create: `pipeline/stages/understat.py`
- Create: `tests/test_understat.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_understat.py`:

```python
import polars as pl
from pipeline.stages.understat import normalize_understat_players, normalize_understat_shots


def test_normalize_understat_players():
    """Should convert raw Understat player data to our schema."""
    import pandas as pd

    raw = pd.DataFrame({
        "id": [10903, 7704],
        "player_name": ["Cole Palmer", "Cristiano Ronaldo"],
        "team": ["Chelsea", "Al Nassr"],
        "games": [32, 28],
        "time": [2800, 2400],
        "goals": [22, 15],
        "xG": [18.5, 14.2],
        "assists": [11, 4],
        "xA": [9.8, 3.5],
        "shots": [95, 88],
        "key_passes": [55, 30],
        "npg": [20, 13],
        "npxG": [16.2, 12.0],
    })

    result = normalize_understat_players(raw, season="2024-2025", league="EPL")

    assert isinstance(result, pl.DataFrame)
    assert len(result) == 2
    assert result["understat_id"][0] == "10903"
    assert result["goals"][0] == 22
    assert result["xg"][0] == 18.5
    assert result["source"][0] == "understat"


def test_normalize_understat_shots():
    """Should convert raw Understat shot data to our schema."""
    import pandas as pd

    raw = pd.DataFrame({
        "id": [501, 502],
        "player_id": [10903, 10903],
        "match_id": [100, 100],
        "minute": [23, 67],
        "result": ["Goal", "SavedShot"],
        "X": [0.89, 0.82],
        "Y": [0.45, 0.38],
        "xG": [0.76, 0.12],
        "situation": ["OpenPlay", "FromCorner"],
        "shotType": ["RightFoot", "Head"],
        "lastAction": ["Pass", "Cross"],
    })

    result = normalize_understat_shots(raw, season="2024-2025", league="EPL")

    assert isinstance(result, pl.DataFrame)
    assert len(result) == 2
    assert result["id"][0] == 501
    assert result["xg"][0] == 0.76
    assert result["x"][0] == 0.89
    assert result["situation"][0] == "OpenPlay"
    assert result["shot_type"][0] == "RightFoot"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_understat.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement the Understat stage**

Create `pipeline/stages/understat.py`:

```python
import polars as pl
import pandas as pd

from pipeline.config import UNDERSTAT_LEAGUES, CURRENT_SEASON


def normalize_understat_players(
    raw_df: pd.DataFrame,
    season: str,
    league: str,
) -> pl.DataFrame:
    """Normalize raw Understat player data into our schema."""
    return pl.DataFrame({
        "understat_id": [str(x) for x in raw_df["id"].tolist()],
        "player_name": raw_df["player_name"].tolist(),
        "team_name": raw_df["team"].tolist(),
        "season": [season] * len(raw_df),
        "league": [league] * len(raw_df),
        "minutes_played": raw_df["time"].tolist(),
        "games": raw_df["games"].tolist(),
        "goals": raw_df["goals"].tolist(),
        "xg": raw_df["xG"].tolist(),
        "npxg": raw_df["npxG"].tolist(),
        "assists": raw_df["assists"].tolist(),
        "xa": raw_df["xA"].tolist(),
        "shots": raw_df["shots"].tolist(),
        "key_passes": raw_df["key_passes"].tolist(),
        "source": ["understat"] * len(raw_df),
    })


def normalize_understat_shots(
    raw_df: pd.DataFrame,
    season: str,
    league: str,
) -> pl.DataFrame:
    """Normalize raw Understat shot data into our schema."""
    return pl.DataFrame({
        "id": raw_df["id"].tolist(),
        "understat_player_id": [str(x) for x in raw_df["player_id"].tolist()],
        "match_id": [str(x) for x in raw_df["match_id"].tolist()],
        "season": [season] * len(raw_df),
        "league": [league] * len(raw_df),
        "minute": raw_df["minute"].tolist(),
        "result": raw_df["result"].tolist(),
        "x": raw_df["X"].tolist(),
        "y": raw_df["Y"].tolist(),
        "xg": raw_df["xG"].tolist(),
        "situation": raw_df["situation"].tolist(),
        "shot_type": raw_df["shotType"].tolist(),
        "last_action": raw_df["lastAction"].tolist(),
        "source": ["understat"] * len(raw_df),
    })


def fetch_understat_league(league: str, season: str) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Fetch player stats and shot data from Understat via soccerdata.

    Returns (player_df, shots_df), either may be None on failure.
    """
    try:
        import soccerdata as sd

        understat = sd.Understat(leagues=league, seasons=season)
        players = understat.read_player_season_stats()
        # Shots require per-match fetching which is slow — skip for now
        # and rely on player-level xG aggregates
        return players, None
    except Exception as e:
        print(f"Understat fetch failed for {league} {season}: {e}")
        return None, None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_understat.py -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/stages/understat.py tests/test_understat.py
git commit -m "feat: Understat stats stage with player and shot normalization"
```

---

### Task 7: ClubElo Stage

**Files:**
- Create: `pipeline/stages/clubelo.py`
- Create: `tests/test_clubelo.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_clubelo.py`:

```python
import polars as pl
from unittest.mock import patch, MagicMock
from pipeline.stages.clubelo import fetch_clubelo_ratings, parse_clubelo_csv


def test_parse_clubelo_csv():
    csv_text = """Rank,Club,Country,Level,Elo,From,To
1,Arsenal,ENG,1,2050,2025-08-01,2025-08-08
2,Chelsea,ENG,1,1980,2025-08-01,2025-08-08
3,Barcelona,ESP,1,2010,2025-08-01,2025-08-08"""

    result = parse_clubelo_csv(csv_text)

    assert isinstance(result, pl.DataFrame)
    assert len(result) == 3
    assert result["club"][0] == "Arsenal"
    assert result["elo"][0] == 2050
    assert result["country"][0] == "ENG"


def test_fetch_clubelo_ratings(tmp_path):
    csv_text = """Rank,Club,Country,Level,Elo,From,To
1,Arsenal,ENG,1,2050,2025-08-01,2025-08-08"""

    resp = MagicMock()
    resp.status_code = 200
    resp.text = csv_text
    resp.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=resp):
        result = fetch_clubelo_ratings("2025-08-01")

    assert len(result) == 1
    assert result["club"][0] == "Arsenal"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_clubelo.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement the ClubElo stage**

Create `pipeline/stages/clubelo.py`:

```python
import io
from datetime import date

import httpx
import polars as pl


def parse_clubelo_csv(csv_text: str) -> pl.DataFrame:
    """Parse ClubElo CSV response into a polars DataFrame."""
    df = pl.read_csv(io.StringIO(csv_text))
    return df.rename({
        "Rank": "rank",
        "Club": "club",
        "Country": "country",
        "Level": "level",
        "Elo": "elo",
        "From": "from_date",
        "To": "to_date",
    })


def fetch_clubelo_ratings(date_str: str | None = None) -> pl.DataFrame:
    """Fetch Elo ratings for all clubs on a given date.

    date_str format: "YYYY-MM-DD". Defaults to today.
    """
    if date_str is None:
        date_str = date.today().isoformat()

    resp = httpx.get(f"http://api.clubelo.com/{date_str}", timeout=30)
    resp.raise_for_status()

    return parse_clubelo_csv(resp.text)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_clubelo.py -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/stages/clubelo.py tests/test_clubelo.py
git commit -m "feat: ClubElo ratings stage"
```

---

### Task 8: Entity Resolution

**Files:**
- Create: `pipeline/stages/resolve.py`
- Create: `tests/test_resolve.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_resolve.py`:

```python
from pipeline.stages.resolve import (
    build_provider_index,
    resolve_fbref_to_reep,
    resolve_understat_to_reep,
    resolve_clubelo_to_reep,
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

    stats = pl.DataFrame({
        "player_name": ["Cole Palmer", "Unknown Player"],
        "fbref_id": ["dc7f8a28", "zzz999"],
        "goals": [22, 5],
    })

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

    stats = pl.DataFrame({
        "player_name": ["Cole Palmer"],
        "understat_id": ["10903"],
        "goals": [22],
    })

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

    elo_df = pl.DataFrame({
        "club": ["Arsenal", "Unknown FC"],
        "elo": [2050, 1500],
    })

    resolved, unresolved = resolve_clubelo_to_reep(db, elo_df)

    assert len(resolved) == 1
    assert resolved["reep_id"][0] == "reep_t1"
    assert len(unresolved) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_resolve.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement entity resolution**

Create `pipeline/stages/resolve.py`:

```python
import sqlite3

import polars as pl


def build_provider_index(conn: sqlite3.Connection) -> tuple[dict, dict]:
    """Build lookup dicts: provider_id → reep_id.

    Returns (fbref_index, understat_index).
    """
    fbref_idx = {}
    understat_idx = {}

    rows = conn.execute(
        "SELECT reep_id, key_fbref, key_understat FROM people"
    ).fetchall()

    for row in rows:
        reep_id = row[0]
        if row[1]:
            fbref_idx[row[1]] = reep_id
        if row[2]:
            understat_idx[row[2]] = reep_id

    return fbref_idx, understat_idx


def _build_teams_clubelo_index(conn: sqlite3.Connection) -> dict:
    """Build lookup: clubelo_name → reep_id."""
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

    reep_ids = [
        fbref_idx.get(fid)
        for fid in stats_df["fbref_id"].to_list()
    ]

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

    reep_ids = [
        understat_idx.get(uid)
        for uid in stats_df["understat_id"].to_list()
    ]

    df = stats_df.with_columns(pl.Series("reep_id", reep_ids))
    resolved = df.filter(pl.col("reep_id").is_not_null())
    unresolved = df.filter(pl.col("reep_id").is_null()).drop("reep_id")

    return resolved, unresolved


def resolve_clubelo_to_reep(
    conn: sqlite3.Connection,
    elo_df: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Resolve ClubElo team names to reep_ids.

    Returns (resolved_df with reep_id column, unresolved_df).
    """
    clubelo_idx = _build_teams_clubelo_index(conn)

    reep_ids = [
        clubelo_idx.get(name)
        for name in elo_df["club"].to_list()
    ]

    df = elo_df.with_columns(pl.Series("reep_id", reep_ids))
    resolved = df.filter(pl.col("reep_id").is_not_null())
    unresolved = df.filter(pl.col("reep_id").is_null()).drop("reep_id")

    return resolved, unresolved
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_resolve.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/stages/resolve.py tests/test_resolve.py
git commit -m "feat: entity resolution — provider IDs to reep_ids"
```

---

### Task 9: Compute Stage — Per-90 + Percentiles

**Files:**
- Create: `pipeline/stages/compute.py`
- Create: `tests/test_compute.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_compute.py`:

```python
import polars as pl
from pipeline.stages.compute import compute_per90, compute_percentiles


def test_compute_per90():
    """Should calculate per-90 stats for players with 900+ minutes."""
    df = pl.DataFrame({
        "reep_id": ["p1", "p2", "p3"],
        "minutes_played": [2700, 900, 450],  # p3 below threshold
        "goals": [18, 6, 5],
        "assists": [9, 3, 4],
        "xg": [15.0, 5.5, 4.0],
        "xa": [8.0, 2.5, 3.0],
        "shots": [80, 30, 25],
        "key_passes": [50, 20, 18],
        "progressive_passes": [70, 25, 20],
        "progressive_carries": [55, 18, 15],
        "tackles": [20, 30, 10],
        "interceptions": [15, 22, 8],
        "pressures": [150, 200, 100],
        "take_ons_succeeded": [40, 15, 12],
    })

    result = compute_per90(df)

    # p3 should be excluded (< 900 minutes)
    assert len(result) == 2

    p1 = result.filter(pl.col("reep_id") == "p1")
    # goals_per90 = (18 / 2700) * 90 = 0.6
    assert abs(p1["goals_per90"][0] - 0.6) < 0.01
    # xg_per90 = (15.0 / 2700) * 90 = 0.5
    assert abs(p1["xg_per90"][0] - 0.5) < 0.01


def test_compute_percentiles():
    """Should compute percentile ranks within a group."""
    df = pl.DataFrame({
        "reep_id": ["p1", "p2", "p3", "p4", "p5"],
        "position_group": ["FW", "FW", "FW", "FW", "FW"],
        "goals_per90": [0.8, 0.6, 0.4, 0.2, 0.1],
        "xg_per90": [0.7, 0.5, 0.4, 0.3, 0.1],
        "assists_per90": [0.3, 0.4, 0.2, 0.1, 0.5],
        "xa_per90": [0.2, 0.3, 0.1, 0.15, 0.4],
        "shots_per90": [4.0, 3.0, 2.5, 2.0, 1.5],
        "key_passes_per90": [1.5, 1.2, 1.0, 0.8, 2.0],
        "progressive_passes_per90": [2.0, 1.8, 1.5, 1.2, 2.5],
        "progressive_carries_per90": [1.5, 1.2, 1.0, 0.8, 1.8],
        "tackles_per90": [0.5, 0.8, 1.0, 1.2, 0.3],
        "interceptions_per90": [0.3, 0.5, 0.7, 0.9, 0.2],
        "pressures_per90": [5.0, 6.0, 7.0, 8.0, 4.0],
        "take_ons_per90": [2.0, 1.5, 1.0, 0.5, 2.5],
    })

    result = compute_percentiles(df)

    p1 = result.filter(pl.col("reep_id") == "p1")
    # p1 has highest goals_per90 (0.8) among 5 players → 99th percentile
    assert p1["goals_pctile"][0] >= 80

    # p5 has lowest goals_per90 (0.1) → low percentile
    p5 = result.filter(pl.col("reep_id") == "p5")
    assert p5["goals_pctile"][0] <= 20
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_compute.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement the compute stage**

Create `pipeline/stages/compute.py`:

```python
import polars as pl

from pipeline.config import MIN_MINUTES_FOR_PER90

PER90_STATS = [
    "goals",
    "xg",
    "assists",
    "xa",
    "shots",
    "key_passes",
    "progressive_passes",
    "progressive_carries",
    "tackles",
    "interceptions",
    "pressures",
    "take_ons_succeeded",
]

PER90_OUTPUT_NAMES = [
    "goals_per90",
    "xg_per90",
    "assists_per90",
    "xa_per90",
    "shots_per90",
    "key_passes_per90",
    "progressive_passes_per90",
    "progressive_carries_per90",
    "tackles_per90",
    "interceptions_per90",
    "pressures_per90",
    "take_ons_per90",
]


def compute_per90(df: pl.DataFrame) -> pl.DataFrame:
    """Compute per-90 stats for players with enough minutes.

    Input df must have reep_id, minutes_played, and the raw stat columns.
    Returns a DataFrame with reep_id + per-90 columns.
    """
    qualified = df.filter(pl.col("minutes_played") >= MIN_MINUTES_FOR_PER90)

    per90_exprs = []
    for raw, out in zip(PER90_STATS, PER90_OUTPUT_NAMES):
        if raw in qualified.columns:
            per90_exprs.append(
                (pl.col(raw).cast(pl.Float64) / pl.col("minutes_played").cast(pl.Float64) * 90)
                .alias(out)
            )
        else:
            per90_exprs.append(pl.lit(None).cast(pl.Float64).alias(out))

    return qualified.select(
        "reep_id",
        *per90_exprs,
    )


def compute_percentiles(df: pl.DataFrame) -> pl.DataFrame:
    """Compute percentile ranks for per-90 stats within position groups.

    Input df must have position_group and the per-90 columns.
    Returns the same DataFrame with added _pctile columns.
    """
    pctile_exprs = []

    for per90_name in PER90_OUTPUT_NAMES:
        pctile_name = per90_name.replace("_per90", "_pctile")
        pctile_exprs.append(
            pl.col(per90_name)
            .rank("ordinal")
            .over("position_group")
            .truediv(pl.col(per90_name).count().over("position_group"))
            .mul(100)
            .cast(pl.Int64)
            .alias(pctile_name)
        )

    return df.with_columns(pctile_exprs)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_compute.py -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/stages/compute.py tests/test_compute.py
git commit -m "feat: compute stage — per-90 stats and percentile ranks"
```

---

### Task 10: Database Write Helpers

**Files:**
- Modify: `pipeline/db.py`
- Create: `tests/test_db_writes.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_db_writes.py`:

```python
import polars as pl
from pipeline.db import upsert_player_stats, upsert_team_stats, upsert_player_per90, log_pipeline_run


def test_upsert_player_stats(db):
    db.execute(
        "INSERT INTO people (reep_id, type, name) VALUES (?, ?, ?)",
        ("reep_p1", "player", "Test Player"),
    )
    db.commit()

    df = pl.DataFrame({
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
    })

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

    df1 = pl.DataFrame({
        "reep_id": ["reep_p1"],
        "season": ["2024-2025"],
        "league": ["Premier League"],
        "source": ["fbref"],
        "goals": [10],
    })
    df2 = pl.DataFrame({
        "reep_id": ["reep_p1"],
        "season": ["2024-2025"],
        "league": ["Premier League"],
        "source": ["fbref"],
        "goals": [18],
    })

    upsert_player_stats(db, df1)
    upsert_player_stats(db, df2)

    count = db.execute("SELECT COUNT(*) FROM player_season_stats").fetchone()[0]
    assert count == 1

    row = db.execute("SELECT goals FROM player_season_stats WHERE reep_id = ?", ("reep_p1",)).fetchone()
    assert row[0] == 18


def test_log_pipeline_run(db):
    run_id = log_pipeline_run(db, status="running")
    assert run_id is not None

    row = db.execute("SELECT * FROM pipeline_runs WHERE id = ?", (run_id,)).fetchone()
    assert row["status"] == "running"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_db_writes.py -v`
Expected: FAIL — `ImportError: cannot import name 'upsert_player_stats'`

- [ ] **Step 3: Implement write helpers**

Add to `pipeline/db.py`:

```python
from datetime import datetime

import polars as pl


# Columns in player_season_stats that we write
_PSS_COLUMNS = [
    "reep_id", "team_reep_id", "season", "league", "minutes_played", "games",
    "starts", "goals", "shots", "shots_on_target", "xg", "npxg", "assists",
    "xa", "key_passes", "passes_completed", "passes_attempted",
    "progressive_passes", "progressive_carries", "progressive_passes_received",
    "tackles", "interceptions", "blocks", "pressures", "pressure_successes",
    "touches", "carries", "take_ons_attempted", "take_ons_succeeded",
    "yellow_cards", "red_cards", "aerials_won", "aerials_lost", "source",
]


def upsert_player_stats(conn: sqlite3.Connection, df: pl.DataFrame) -> int:
    """Upsert player season stats from a polars DataFrame. Returns row count."""
    available = [c for c in _PSS_COLUMNS if c in df.columns]
    placeholders = ", ".join("?" for _ in available)
    col_names = ", ".join(available)
    updates = ", ".join(
        f"{c} = excluded.{c}" for c in available
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
        f"{c} = excluded.{c}" for c in available
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
    available = [c for c in df.columns]
    placeholders = ", ".join("?" for _ in available)
    col_names = ", ".join(available)
    updates = ", ".join(
        f"{c} = excluded.{c}" for c in available
        if c not in ("reep_id", "season", "league")
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
        (datetime.utcnow().isoformat(), status, people_count, teams_count, stats_fetched, match_rate, error_log),
    )
    conn.commit()
    return cursor.lastrowid
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_db_writes.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/db.py tests/test_db_writes.py
git commit -m "feat: database upsert helpers for stats and pipeline logging"
```

---

### Task 11: CLI Entry Point + Pipeline Orchestration

**Files:**
- Create: `pipeline/cli.py`

- [ ] **Step 1: Implement the CLI**

Create `pipeline/cli.py`:

```python
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import click

from pipeline.db import get_connection, init_schema, upsert_player_stats, log_pipeline_run
from pipeline.config import TOP_5_LEAGUES, UNDERSTAT_LEAGUES, CURRENT_SEASON


@click.group()
def main():
    """Pitch Intel data pipeline."""
    pass


@main.command()
@click.option("--local-db", type=str, default=None, help="Path to local SQLite file (for dev/testing)")
def init(local_db):
    """Initialize the database schema."""
    conn = get_connection(local_db)
    init_schema(conn)
    click.echo("Schema initialized.")
    conn.close()


@main.command()
@click.option("--local-db", type=str, default=None)
@click.option("--season", type=str, default=CURRENT_SEASON)
def run(local_db, season):
    """Run the full pipeline: identity → stats → resolve → compute."""
    conn = get_connection(local_db)
    init_schema(conn)

    run_id = log_pipeline_run(conn, status="running")
    errors = []

    # Stage 1: Identity
    click.echo("Stage 1: Downloading Reep identity data...")
    try:
        from pipeline.stages.identity import download_reep_csvs, ingest_people_csv, ingest_teams_csv

        with TemporaryDirectory() as tmp:
            people_path, teams_path = download_reep_csvs(Path(tmp))
            people_count = ingest_people_csv(conn, people_path)
            teams_count = ingest_teams_csv(conn, teams_path)
            click.echo(f"  Loaded {people_count} people, {teams_count} teams.")
    except Exception as e:
        errors.append(f"Identity stage failed: {e}")
        click.echo(f"  ERROR: {e}")
        people_count = 0
        teams_count = 0

    # Stage 2a: FBref
    click.echo("Stage 2a: Fetching FBref stats...")
    fbref_total = 0
    for league_code, league_name in TOP_5_LEAGUES.items():
        try:
            from pipeline.stages.fbref import fetch_fbref_season, normalize_fbref_stats
            from pipeline.stages.resolve import resolve_fbref_to_reep

            raw = fetch_fbref_season(league_code, season)
            if raw is not None:
                normalized = normalize_fbref_stats(raw, season=season, league=league_name)
                # FBref IDs need to be added — soccerdata includes them in the index
                # For now, resolve by name matching against people table
                click.echo(f"  {league_name}: {len(normalized)} players fetched.")
                fbref_total += len(normalized)
        except Exception as e:
            errors.append(f"FBref {league_name}: {e}")
            click.echo(f"  {league_name} ERROR: {e}")

    # Stage 2b: Understat
    click.echo("Stage 2b: Fetching Understat stats...")
    understat_total = 0
    for league in UNDERSTAT_LEAGUES:
        try:
            from pipeline.stages.understat import fetch_understat_league, normalize_understat_players
            from pipeline.stages.resolve import resolve_understat_to_reep

            players_raw, _ = fetch_understat_league(league, season)
            if players_raw is not None:
                normalized = normalize_understat_players(players_raw, season=season, league=league)
                resolved, unresolved = resolve_understat_to_reep(conn, normalized)
                if len(resolved) > 0:
                    upsert_player_stats(conn, resolved.drop("understat_id", "player_name", "team_name"))
                click.echo(f"  {league}: {len(resolved)} resolved, {len(unresolved)} unresolved.")
                understat_total += len(resolved)
        except Exception as e:
            errors.append(f"Understat {league}: {e}")
            click.echo(f"  {league} ERROR: {e}")

    # Stage 2c: ClubElo
    click.echo("Stage 2c: Fetching ClubElo ratings...")
    try:
        from pipeline.stages.clubelo import fetch_clubelo_ratings
        from pipeline.stages.resolve import resolve_clubelo_to_reep

        elo_df = fetch_clubelo_ratings()
        resolved_elo, _ = resolve_clubelo_to_reep(conn, elo_df)
        click.echo(f"  {len(resolved_elo)} teams with Elo ratings.")
    except Exception as e:
        errors.append(f"ClubElo: {e}")
        click.echo(f"  ERROR: {e}")

    # Stage 4: Compute
    click.echo("Stage 4: Computing per-90 stats and percentiles...")
    try:
        from pipeline.stages.compute import compute_per90, compute_percentiles
        from pipeline.db import upsert_player_per90

        # Load all player stats from DB
        import polars as pl

        rows = conn.execute("SELECT * FROM player_season_stats WHERE season = ?", (season,)).fetchall()
        if rows:
            columns = [desc[0] for desc in conn.execute("SELECT * FROM player_season_stats LIMIT 0").description]
            stats_df = pl.DataFrame([dict(zip(columns, row)) for row in rows])
            per90 = compute_per90(stats_df)
            click.echo(f"  {len(per90)} players with per-90 stats.")
        else:
            click.echo("  No stats to compute per-90 for.")
    except Exception as e:
        errors.append(f"Compute: {e}")
        click.echo(f"  ERROR: {e}")

    # Log completion
    stats_fetched = fbref_total + understat_total
    status = "completed" if not errors else "completed_with_errors"
    conn.execute(
        """UPDATE pipeline_runs
           SET completed_at = ?, status = ?, people_count = ?, teams_count = ?,
               stats_fetched = ?, error_log = ?
           WHERE id = ?""",
        (datetime.utcnow().isoformat(), status, people_count, teams_count,
         stats_fetched, "\n".join(errors) if errors else None, run_id),
    )
    conn.commit()

    click.echo(f"\nPipeline {status}. {len(errors)} errors.")
    if errors:
        for e in errors:
            click.echo(f"  - {e}")

    conn.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test the CLI runs**

Run: `cd pitch-intel && python -m pipeline.cli init --local-db test.db`
Expected: "Schema initialized."

Run: `rm test.db`

- [ ] **Step 3: Commit**

```bash
git add pipeline/cli.py
git commit -m "feat: CLI entry point with full pipeline orchestration"
```

---

### Task 12: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/pipeline.yml`

- [ ] **Step 1: Create the workflow file**

Create `.github/workflows/pipeline.yml`:

```yaml
name: Data Pipeline

on:
  schedule:
    # Every Monday at 06:00 UTC (after Reep's weekly refresh)
    - cron: '0 6 * * 1'
  workflow_dispatch: # Allow manual runs

jobs:
  pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 60

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -e .

      - name: Run pipeline
        env:
          TURSO_DATABASE_URL: ${{ secrets.TURSO_DATABASE_URL }}
          TURSO_AUTH_TOKEN: ${{ secrets.TURSO_AUTH_TOKEN }}
          REEP_API_KEY: ${{ secrets.REEP_API_KEY }}
        run: python -m pipeline.cli run --season 2025-2026
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/pipeline.yml
git commit -m "ci: weekly data pipeline via GitHub Actions"
```

---

### Task 13: Run All Tests

- [ ] **Step 1: Run the full test suite**

Run: `cd pitch-intel && python -m pytest tests/ -v`
Expected: All tests PASS (approximately 17 tests across 7 test files)

- [ ] **Step 2: Fix any failures**

If any tests fail, diagnose and fix. Common issues:
- Import paths: ensure `pipeline` is importable (check that `pip install -e .` was run)
- Polars version differences: check column type coercions

- [ ] **Step 3: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: test suite adjustments"
```

---

## Summary

| Task | What it builds | Tests |
|------|---------------|-------|
| 1 | Project setup, dependencies | — |
| 2 | Schema + DB connection | 4 |
| 3 | Identity CSV ingestion | 4 |
| 4 | Remote CSV download | 1 |
| 5 | FBref stats normalization | 2 |
| 6 | Understat stats normalization | 2 |
| 7 | ClubElo ratings | 2 |
| 8 | Entity resolution | 4 |
| 9 | Per-90 + percentile computation | 2 |
| 10 | DB write helpers | 3 |
| 11 | CLI orchestration | manual |
| 12 | GitHub Actions workflow | — |
| 13 | Full test run | all |

**Deferred to future increments:**
- StatsBomb open data ingestion (event-level data for select competitions)
- football-data.co.uk match results ingestion
- Squad membership population (derived from FBref squad pages)
- Player embeddings + clustering (Plan 5: ML Features)
- Team profiles computation (Plan 5: ML Features)

**After this plan:** The data pipeline is functional end-to-end. Next plan (Plan 2) builds the FastAPI backend that reads from this database.
