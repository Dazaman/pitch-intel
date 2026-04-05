# Backend API Implementation Plan (Plan 2 of 5)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI backend that serves player/team data from Turso to the frontend via REST endpoints.

**Architecture:** FastAPI app with Pydantic response models. Reuses `pipeline.db.get_connection` for database access. Endpoints read from the tables populated by the data pipeline (Plan 1). CORS enabled for the Vercel frontend.

**Tech Stack:** FastAPI, Pydantic, uvicorn, pipeline.db (existing), uv, ruff

---

## Scope

This plan covers the **data-serving endpoints** — everything the frontend needs to display player/team profiles, stats, radars, comparisons, and search. ML-powered endpoints (similar, fit, gaps, clusters) are deferred to Plan 5.

**Included (12 endpoints):**
- `GET /api/health`
- `GET /api/search?q={name}&type={player|team}`
- `GET /api/player/{reep_id}`
- `GET /api/player/{reep_id}/stats?season={season}`
- `GET /api/player/{reep_id}/shots?season={season}`
- `GET /api/player/{reep_id}/radar?season={season}`
- `GET /api/team/{reep_id}`
- `GET /api/team/{reep_id}/stats?season={season}`
- `GET /api/team/{reep_id}/squad?season={season}`
- `GET /api/compare/players?ids={id1,id2,id3}`
- `GET /api/compare/teams?ids={id1,id2}`
- `GET /api/explore/scatter?x={stat}&y={stat}&league={league}&position={pos}`

**Deferred to Plan 5 (ML Features):**
- `GET /api/player/{reep_id}/similar?n={10}`
- `GET /api/player/{reep_id}/fit?team={reep_id}`
- `GET /api/team/{reep_id}/profile?season={season}`
- `GET /api/team/{reep_id}/gaps?season={season}`
- `GET /api/explore/clusters?season={season}`

## File Structure

```
pitch-intel/
├── api/
│   ├── __init__.py
│   ├── app.py              # FastAPI app, CORS, lifespan (DB connection)
│   ├── deps.py             # Dependency injection (get DB connection)
│   ├── models.py           # Pydantic response models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py       # GET /api/health
│   │   ├── search.py       # GET /api/search
│   │   ├── players.py      # GET /api/player/* endpoints
│   │   ├── teams.py        # GET /api/team/* endpoints
│   │   ├── compare.py      # GET /api/compare/* endpoints
│   │   └── explore.py      # GET /api/explore/* endpoints
│   └── queries.py          # Raw SQL queries as named constants
├── tests/
│   ├── test_api_health.py
│   ├── test_api_search.py
│   ├── test_api_players.py
│   ├── test_api_teams.py
│   ├── test_api_compare.py
│   └── test_api_explore.py
└── pyproject.toml          # Add fastapi, uvicorn deps
```

---

### Task 1: Add FastAPI Dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add FastAPI and uvicorn to dependencies**

In `pyproject.toml`, add to the `dependencies` list:
```toml
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
```

- [ ] **Step 2: Install**

Run: `uv sync`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add FastAPI and uvicorn dependencies"
```

---

### Task 2: Pydantic Models + Query Constants

**Files:**
- Create: `api/__init__.py`
- Create: `api/models.py`
- Create: `api/queries.py`
- Create: `api/routers/__init__.py`

- [ ] **Step 1: Create `api/__init__.py`** (empty)

- [ ] **Step 2: Create `api/routers/__init__.py`** (empty)

- [ ] **Step 3: Create `api/models.py`**

```python
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    last_pipeline_run: str | None = None
    people_count: int | None = None
    teams_count: int | None = None


class PersonSummary(BaseModel):
    reep_id: str
    type: str
    name: str
    nationality: str | None = None
    position: str | None = None
    date_of_birth: str | None = None


class TeamSummary(BaseModel):
    reep_id: str
    name: str
    country: str | None = None
    stadium: str | None = None


class SearchResponse(BaseModel):
    results: list[PersonSummary | TeamSummary]
    count: int


class PlayerProfile(BaseModel):
    reep_id: str
    type: str
    name: str
    full_name: str | None = None
    date_of_birth: str | None = None
    nationality: str | None = None
    position: str | None = None
    height_cm: int | None = None
    key_transfermarkt: str | None = None
    key_fbref: str | None = None


class PlayerSeasonStats(BaseModel):
    season: str
    league: str
    source: str
    minutes_played: int | None = None
    games: int | None = None
    starts: int | None = None
    goals: int | None = None
    assists: int | None = None
    xg: float | None = None
    npxg: float | None = None
    xa: float | None = None
    shots: int | None = None
    shots_on_target: int | None = None
    key_passes: int | None = None
    passes_completed: int | None = None
    passes_attempted: int | None = None
    progressive_passes: int | None = None
    progressive_carries: int | None = None
    tackles: int | None = None
    interceptions: int | None = None
    pressures: int | None = None
    take_ons_attempted: int | None = None
    take_ons_succeeded: int | None = None
    yellow_cards: int | None = None
    red_cards: int | None = None


class ShotData(BaseModel):
    id: int
    minute: int | None = None
    result: str | None = None
    x: float | None = None
    y: float | None = None
    xg: float | None = None
    situation: str | None = None
    shot_type: str | None = None


class RadarData(BaseModel):
    reep_id: str
    season: str
    league: str
    position_group: str
    minutes_played: int
    stats: dict[str, float | None]
    percentiles: dict[str, int | None]


class TeamProfile(BaseModel):
    reep_id: str
    name: str
    country: str | None = None
    founded: str | None = None
    stadium: str | None = None
    key_transfermarkt: str | None = None
    key_fbref: str | None = None


class TeamSeasonStats(BaseModel):
    season: str
    league: str
    source: str
    wins: int | None = None
    draws: int | None = None
    losses: int | None = None
    goals_for: int | None = None
    goals_against: int | None = None
    xg: float | None = None
    xga: float | None = None
    ppda: float | None = None
    elo_start: float | None = None
    elo_end: float | None = None


class SquadMember(BaseModel):
    reep_id: str
    name: str
    position: str | None = None
    nationality: str | None = None
    date_of_birth: str | None = None
    minutes_played: int | None = None
    goals: int | None = None
    assists: int | None = None
    xg: float | None = None


class ScatterPoint(BaseModel):
    reep_id: str
    name: str
    position: str | None = None
    league: str
    x_value: float | None = None
    y_value: float | None = None
```

- [ ] **Step 4: Create `api/queries.py`**

```python
SEARCH_PEOPLE = """
    SELECT reep_id, type, name, nationality, position, date_of_birth
    FROM people
    WHERE name LIKE ? COLLATE NOCASE
    ORDER BY name
    LIMIT 20
"""

SEARCH_TEAMS = """
    SELECT reep_id, name, country, stadium
    FROM teams
    WHERE name LIKE ? COLLATE NOCASE
    ORDER BY name
    LIMIT 20
"""

GET_PLAYER = """
    SELECT reep_id, type, name, full_name, date_of_birth, nationality,
           position, height_cm, key_transfermarkt, key_fbref
    FROM people
    WHERE reep_id = ?
"""

GET_PLAYER_STATS = """
    SELECT season, league, source, minutes_played, games, starts,
           goals, assists, xg, npxg, xa, shots, shots_on_target,
           key_passes, passes_completed, passes_attempted,
           progressive_passes, progressive_carries,
           tackles, interceptions, pressures,
           take_ons_attempted, take_ons_succeeded,
           yellow_cards, red_cards
    FROM player_season_stats
    WHERE reep_id = ?
    ORDER BY season DESC
"""

GET_PLAYER_STATS_BY_SEASON = """
    SELECT season, league, source, minutes_played, games, starts,
           goals, assists, xg, npxg, xa, shots, shots_on_target,
           key_passes, passes_completed, passes_attempted,
           progressive_passes, progressive_carries,
           tackles, interceptions, pressures,
           take_ons_attempted, take_ons_succeeded,
           yellow_cards, red_cards
    FROM player_season_stats
    WHERE reep_id = ? AND season = ?
    ORDER BY league
"""

GET_PLAYER_SHOTS = """
    SELECT id, minute, result, x, y, xg, situation, shot_type
    FROM shots
    WHERE reep_id = ?
    ORDER BY minute
"""

GET_PLAYER_SHOTS_BY_SEASON = """
    SELECT id, minute, result, x, y, xg, situation, shot_type
    FROM shots
    WHERE reep_id = ? AND season = ?
    ORDER BY minute
"""

GET_PLAYER_RADAR = """
    SELECT reep_id, season, league, position_group, minutes_played,
           goals_per90, xg_per90, assists_per90, xa_per90,
           shots_per90, key_passes_per90,
           progressive_passes_per90, progressive_carries_per90,
           tackles_per90, interceptions_per90, pressures_per90, take_ons_per90,
           goals_pctile, xg_pctile, assists_pctile, xa_pctile,
           shots_pctile, key_passes_pctile,
           progressive_passes_pctile, progressive_carries_pctile,
           tackles_pctile, interceptions_pctile, pressures_pctile, take_ons_pctile
    FROM player_per90
    WHERE reep_id = ?
    ORDER BY season DESC
    LIMIT 1
"""

GET_PLAYER_RADAR_BY_SEASON = """
    SELECT reep_id, season, league, position_group, minutes_played,
           goals_per90, xg_per90, assists_per90, xa_per90,
           shots_per90, key_passes_per90,
           progressive_passes_per90, progressive_carries_per90,
           tackles_per90, interceptions_per90, pressures_per90, take_ons_per90,
           goals_pctile, xg_pctile, assists_pctile, xa_pctile,
           shots_pctile, key_passes_pctile,
           progressive_passes_pctile, progressive_carries_pctile,
           tackles_pctile, interceptions_pctile, pressures_pctile, take_ons_pctile
    FROM player_per90
    WHERE reep_id = ? AND season = ?
    LIMIT 1
"""

GET_TEAM = """
    SELECT reep_id, name, country, founded, stadium,
           key_transfermarkt, key_fbref
    FROM teams
    WHERE reep_id = ?
"""

GET_TEAM_STATS = """
    SELECT season, league, source, wins, draws, losses,
           goals_for, goals_against, xg, xga, ppda,
           elo_start, elo_end
    FROM team_season_stats
    WHERE reep_id = ?
    ORDER BY season DESC
"""

GET_TEAM_STATS_BY_SEASON = """
    SELECT season, league, source, wins, draws, losses,
           goals_for, goals_against, xg, xga, ppda,
           elo_start, elo_end
    FROM team_season_stats
    WHERE reep_id = ? AND season = ?
"""

GET_TEAM_SQUAD = """
    SELECT p.reep_id, p.name, p.position, p.nationality, p.date_of_birth,
           s.minutes_played, s.goals, s.assists, s.xg
    FROM squad_membership sm
    JOIN people p ON sm.reep_id = p.reep_id
    LEFT JOIN player_season_stats s
        ON sm.reep_id = s.reep_id AND sm.season = s.season AND sm.league = s.league
    WHERE sm.team_reep_id = ? AND sm.season = ?
    ORDER BY p.position, p.name
"""

HEALTH_CHECK = """
    SELECT status, started_at, people_count, teams_count
    FROM pipeline_runs
    ORDER BY id DESC
    LIMIT 1
"""

SCATTER_QUERY = """
    SELECT p90.reep_id, pe.name, pe.position, p90.league,
           p90.{x_stat} as x_value, p90.{y_stat} as y_value
    FROM player_per90 p90
    JOIN people pe ON p90.reep_id = pe.reep_id
    WHERE p90.{x_stat} IS NOT NULL AND p90.{y_stat} IS NOT NULL
"""
```

- [ ] **Step 5: Run ruff**

Run: `uv run ruff check api/ && uv run ruff format api/`

- [ ] **Step 6: Commit**

```bash
git add api/
git commit -m "feat: Pydantic models and SQL query constants"
```

---

### Task 3: App Setup + Health Endpoint + DB Dependency

**Files:**
- Create: `api/app.py`
- Create: `api/deps.py`
- Create: `api/routers/health.py`
- Create: `tests/test_api_health.py`

- [ ] **Step 1: Create `api/deps.py`**

```python
import sqlite3
from contextlib import contextmanager

from pipeline.db import get_connection, init_schema

_conn: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    """Return the shared DB connection. Creates it on first call."""
    global _conn
    if _conn is None:
        _conn = get_connection()
        _conn.row_factory = sqlite3.Row
        init_schema(_conn)
    return _conn


def override_db(conn: sqlite3.Connection) -> None:
    """Override the DB connection (for testing)."""
    global _conn
    _conn = conn
```

- [ ] **Step 2: Create `api/routers/health.py`**

```python
from fastapi import APIRouter

from api.deps import get_db
from api.models import HealthResponse
from api.queries import HEALTH_CHECK

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    conn = get_db()
    row = conn.execute(HEALTH_CHECK).fetchone()

    if row:
        return HealthResponse(
            status=row["status"],
            last_pipeline_run=row["started_at"],
            people_count=row["people_count"],
            teams_count=row["teams_count"],
        )

    # No pipeline runs yet — check if tables exist
    people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    teams = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]

    return HealthResponse(
        status="no_pipeline_runs",
        people_count=people,
        teams_count=teams,
    )
```

- [ ] **Step 3: Create `api/app.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import compare, explore, health, players, search, teams

app = FastAPI(title="Pitch Intel API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(players.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(explore.router, prefix="/api")
```

Note: This will fail to import until all routers exist. Create stubs for the missing routers so the app can start. Each stub is just:

```python
from fastapi import APIRouter
router = APIRouter()
```

Create these stubs now at: `api/routers/search.py`, `api/routers/players.py`, `api/routers/teams.py`, `api/routers/compare.py`, `api/routers/explore.py`

- [ ] **Step 4: Write the test**

Create `tests/test_api_health.py`:

```python
from fastapi.testclient import TestClient

from api.app import app
from api.deps import override_db


def _setup_test_db():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from pipeline.db import init_schema
    init_schema(conn)
    override_db(conn)
    return conn


def test_health_no_pipeline_runs():
    conn = _setup_test_db()
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "no_pipeline_runs"
    assert data["people_count"] == 0


def test_health_with_pipeline_run():
    conn = _setup_test_db()
    conn.execute(
        """INSERT INTO pipeline_runs (started_at, status, people_count, teams_count)
           VALUES (?, ?, ?, ?)""",
        ("2026-04-06T10:00:00", "completed", 488000, 45000),
    )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["people_count"] == 488000
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_api_health.py -v`
Expected: 2 tests PASS

- [ ] **Step 6: Run ruff**

Run: `uv run ruff check api/ tests/test_api_health.py && uv run ruff format api/ tests/test_api_health.py`

- [ ] **Step 7: Commit**

```bash
git add api/ tests/test_api_health.py
git commit -m "feat: FastAPI app with health endpoint and DB dependency"
```

---

### Task 4: Search Endpoint

**Files:**
- Modify: `api/routers/search.py`
- Create: `tests/test_api_search.py`

- [ ] **Step 1: Implement search router**

Replace the stub in `api/routers/search.py`:

```python
from fastapi import APIRouter, Query

from api.deps import get_db
from api.models import PersonSummary, SearchResponse, TeamSummary
from api.queries import SEARCH_PEOPLE, SEARCH_TEAMS

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(min_length=2),
    type: str | None = Query(default=None, pattern="^(player|team)$"),
):
    conn = get_db()
    pattern = f"%{q}%"
    results: list[PersonSummary | TeamSummary] = []

    if type is None or type == "player":
        rows = conn.execute(SEARCH_PEOPLE, (pattern,)).fetchall()
        results.extend(PersonSummary(**dict(row)) for row in rows)

    if type is None or type == "team":
        rows = conn.execute(SEARCH_TEAMS, (pattern,)).fetchall()
        results.extend(TeamSummary(**dict(row)) for row in rows)

    return SearchResponse(results=results, count=len(results))
```

- [ ] **Step 2: Write tests**

Create `tests/test_api_search.py`:

```python
from fastapi.testclient import TestClient

from api.app import app
from api.deps import override_db


def _setup_test_db():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from pipeline.db import init_schema
    init_schema(conn)
    override_db(conn)
    return conn


def test_search_players():
    conn = _setup_test_db()
    conn.execute(
        "INSERT INTO people (reep_id, type, name, nationality, position) VALUES (?, ?, ?, ?, ?)",
        ("reep_p1", "player", "Cole Palmer", "United Kingdom", "attacking midfielder"),
    )
    conn.execute(
        "INSERT INTO people (reep_id, type, name, nationality, position) VALUES (?, ?, ?, ?, ?)",
        ("reep_p2", "player", "Bukayo Saka", "United Kingdom", "right winger"),
    )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/search?q=Palmer&type=player")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Cole Palmer"


def test_search_teams():
    conn = _setup_test_db()
    conn.execute(
        "INSERT INTO teams (reep_id, name, country) VALUES (?, ?, ?)",
        ("reep_t1", "Arsenal F.C.", "United Kingdom"),
    )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/search?q=Arsenal&type=team")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Arsenal F.C."


def test_search_all_types():
    conn = _setup_test_db()
    conn.execute(
        "INSERT INTO people (reep_id, type, name) VALUES (?, ?, ?)",
        ("reep_p1", "player", "Martin Arsenal"),
    )
    conn.execute(
        "INSERT INTO teams (reep_id, name) VALUES (?, ?)",
        ("reep_t1", "Arsenal F.C."),
    )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/search?q=Arsenal")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2


def test_search_min_length():
    _setup_test_db()
    client = TestClient(app)
    resp = client.get("/api/search?q=a")
    assert resp.status_code == 422
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_api_search.py -v`
Expected: 4 tests PASS

- [ ] **Step 4: Run ruff + commit**

```bash
uv run ruff check api/routers/search.py tests/test_api_search.py && uv run ruff format api/routers/search.py tests/test_api_search.py
git add api/routers/search.py tests/test_api_search.py
git commit -m "feat: search endpoint with player and team support"
```

---

### Task 5: Player Endpoints

**Files:**
- Modify: `api/routers/players.py`
- Create: `tests/test_api_players.py`

- [ ] **Step 1: Implement players router**

Replace the stub in `api/routers/players.py`:

```python
from fastapi import APIRouter, HTTPException, Query

from api.deps import get_db
from api.models import PlayerProfile, PlayerSeasonStats, RadarData, ShotData
from api.queries import (
    GET_PLAYER,
    GET_PLAYER_RADAR,
    GET_PLAYER_RADAR_BY_SEASON,
    GET_PLAYER_SHOTS,
    GET_PLAYER_SHOTS_BY_SEASON,
    GET_PLAYER_STATS,
    GET_PLAYER_STATS_BY_SEASON,
)

router = APIRouter()

PER90_FIELDS = [
    "goals_per90", "xg_per90", "assists_per90", "xa_per90",
    "shots_per90", "key_passes_per90",
    "progressive_passes_per90", "progressive_carries_per90",
    "tackles_per90", "interceptions_per90", "pressures_per90", "take_ons_per90",
]

PCTILE_FIELDS = [
    "goals_pctile", "xg_pctile", "assists_pctile", "xa_pctile",
    "shots_pctile", "key_passes_pctile",
    "progressive_passes_pctile", "progressive_carries_pctile",
    "tackles_pctile", "interceptions_pctile", "pressures_pctile", "take_ons_pctile",
]


@router.get("/player/{reep_id}", response_model=PlayerProfile)
def get_player(reep_id: str):
    conn = get_db()
    row = conn.execute(GET_PLAYER, (reep_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Player not found")
    return PlayerProfile(**dict(row))


@router.get("/player/{reep_id}/stats", response_model=list[PlayerSeasonStats])
def get_player_stats(reep_id: str, season: str | None = Query(default=None)):
    conn = get_db()
    if season:
        rows = conn.execute(GET_PLAYER_STATS_BY_SEASON, (reep_id, season)).fetchall()
    else:
        rows = conn.execute(GET_PLAYER_STATS, (reep_id,)).fetchall()
    return [PlayerSeasonStats(**dict(row)) for row in rows]


@router.get("/player/{reep_id}/shots", response_model=list[ShotData])
def get_player_shots(reep_id: str, season: str | None = Query(default=None)):
    conn = get_db()
    if season:
        rows = conn.execute(GET_PLAYER_SHOTS_BY_SEASON, (reep_id, season)).fetchall()
    else:
        rows = conn.execute(GET_PLAYER_SHOTS, (reep_id,)).fetchall()
    return [ShotData(**dict(row)) for row in rows]


@router.get("/player/{reep_id}/radar", response_model=RadarData | None)
def get_player_radar(reep_id: str, season: str | None = Query(default=None)):
    conn = get_db()
    if season:
        row = conn.execute(GET_PLAYER_RADAR_BY_SEASON, (reep_id, season)).fetchone()
    else:
        row = conn.execute(GET_PLAYER_RADAR, (reep_id,)).fetchone()

    if not row:
        return None

    row_dict = dict(row)
    stats = {f: row_dict.get(f) for f in PER90_FIELDS}
    percentiles = {f: row_dict.get(f) for f in PCTILE_FIELDS}

    return RadarData(
        reep_id=row_dict["reep_id"],
        season=row_dict["season"],
        league=row_dict["league"],
        position_group=row_dict["position_group"],
        minutes_played=row_dict["minutes_played"],
        stats=stats,
        percentiles=percentiles,
    )
```

- [ ] **Step 2: Write tests**

Create `tests/test_api_players.py`:

```python
from fastapi.testclient import TestClient

from api.app import app
from api.deps import override_db


def _setup_test_db():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from pipeline.db import init_schema
    init_schema(conn)
    override_db(conn)
    return conn


def _seed_player(conn):
    conn.execute(
        """INSERT INTO people (reep_id, type, name, full_name, nationality, position, height_cm)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("reep_p1", "player", "Cole Palmer", "Cole Jermaine Palmer", "United Kingdom", "attacking midfielder", 185),
    )
    conn.execute(
        """INSERT INTO player_season_stats
           (reep_id, season, league, source, minutes_played, games, goals, assists, xg, xa)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("reep_p1", "2024-2025", "Premier League", "fbref", 2700, 32, 22, 11, 18.5, 9.8),
    )
    conn.execute(
        """INSERT INTO shots (id, reep_id, season, league, minute, result, x, y, xg, situation, shot_type, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (501, "reep_p1", "2024-2025", "Premier League", 23, "Goal", 0.89, 0.45, 0.76, "OpenPlay", "RightFoot", "understat"),
    )
    conn.execute(
        """INSERT INTO player_per90
           (reep_id, season, league, position_group, minutes_played,
            goals_per90, xg_per90, assists_per90, xa_per90,
            shots_per90, key_passes_per90, progressive_passes_per90, progressive_carries_per90,
            tackles_per90, interceptions_per90, pressures_per90, take_ons_per90,
            goals_pctile, xg_pctile, assists_pctile, xa_pctile,
            shots_pctile, key_passes_pctile, progressive_passes_pctile, progressive_carries_pctile,
            tackles_pctile, interceptions_pctile, pressures_pctile, take_ons_pctile)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("reep_p1", "2024-2025", "Premier League", "MF", 2700,
         0.73, 0.62, 0.37, 0.33, 2.67, 1.67, 2.33, 1.83, 0.67, 0.5, 5.0, 1.33,
         95, 90, 88, 85, 92, 80, 78, 75, 30, 25, 40, 70),
    )
    conn.commit()


def test_get_player():
    conn = _setup_test_db()
    _seed_player(conn)

    client = TestClient(app)
    resp = client.get("/api/player/reep_p1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Cole Palmer"
    assert data["height_cm"] == 185


def test_get_player_not_found():
    _setup_test_db()
    client = TestClient(app)
    resp = client.get("/api/player/reep_pXXXXXX")
    assert resp.status_code == 404


def test_get_player_stats():
    conn = _setup_test_db()
    _seed_player(conn)

    client = TestClient(app)
    resp = client.get("/api/player/reep_p1/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["goals"] == 22
    assert data[0]["xg"] == 18.5


def test_get_player_shots():
    conn = _setup_test_db()
    _seed_player(conn)

    client = TestClient(app)
    resp = client.get("/api/player/reep_p1/shots?season=2024-2025")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["result"] == "Goal"
    assert data[0]["xg"] == 0.76


def test_get_player_radar():
    conn = _setup_test_db()
    _seed_player(conn)

    client = TestClient(app)
    resp = client.get("/api/player/reep_p1/radar")
    assert resp.status_code == 200
    data = resp.json()
    assert data["position_group"] == "MF"
    assert data["stats"]["goals_per90"] == 0.73
    assert data["percentiles"]["goals_pctile"] == 95
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_api_players.py -v`
Expected: 5 tests PASS

- [ ] **Step 4: Run ruff + commit**

```bash
uv run ruff check api/routers/players.py tests/test_api_players.py && uv run ruff format api/routers/players.py tests/test_api_players.py
git add api/routers/players.py tests/test_api_players.py
git commit -m "feat: player profile, stats, shots, and radar endpoints"
```

---

### Task 6: Team Endpoints

**Files:**
- Modify: `api/routers/teams.py`
- Create: `tests/test_api_teams.py`

- [ ] **Step 1: Implement teams router**

Replace the stub in `api/routers/teams.py`:

```python
from fastapi import APIRouter, HTTPException, Query

from api.deps import get_db
from api.models import SquadMember, TeamProfile, TeamSeasonStats
from api.queries import GET_TEAM, GET_TEAM_SQUAD, GET_TEAM_STATS, GET_TEAM_STATS_BY_SEASON

router = APIRouter()


@router.get("/team/{reep_id}", response_model=TeamProfile)
def get_team(reep_id: str):
    conn = get_db()
    row = conn.execute(GET_TEAM, (reep_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamProfile(**dict(row))


@router.get("/team/{reep_id}/stats", response_model=list[TeamSeasonStats])
def get_team_stats(reep_id: str, season: str | None = Query(default=None)):
    conn = get_db()
    if season:
        rows = conn.execute(GET_TEAM_STATS_BY_SEASON, (reep_id, season)).fetchall()
    else:
        rows = conn.execute(GET_TEAM_STATS, (reep_id,)).fetchall()
    return [TeamSeasonStats(**dict(row)) for row in rows]


@router.get("/team/{reep_id}/squad", response_model=list[SquadMember])
def get_team_squad(reep_id: str, season: str = Query()):
    conn = get_db()
    rows = conn.execute(GET_TEAM_SQUAD, (reep_id, season)).fetchall()
    return [SquadMember(**dict(row)) for row in rows]
```

- [ ] **Step 2: Write tests**

Create `tests/test_api_teams.py`:

```python
from fastapi.testclient import TestClient

from api.app import app
from api.deps import override_db


def _setup_test_db():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from pipeline.db import init_schema
    init_schema(conn)
    override_db(conn)
    return conn


def test_get_team():
    conn = _setup_test_db()
    conn.execute(
        "INSERT INTO teams (reep_id, name, country, stadium) VALUES (?, ?, ?, ?)",
        ("reep_t1", "Arsenal F.C.", "United Kingdom", "Emirates Stadium"),
    )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/team/reep_t1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Arsenal F.C."
    assert data["stadium"] == "Emirates Stadium"


def test_get_team_not_found():
    _setup_test_db()
    client = TestClient(app)
    resp = client.get("/api/team/reep_tXXXXXX")
    assert resp.status_code == 404


def test_get_team_stats():
    conn = _setup_test_db()
    conn.execute(
        "INSERT INTO teams (reep_id, name) VALUES (?, ?)",
        ("reep_t1", "Arsenal F.C."),
    )
    conn.execute(
        """INSERT INTO team_season_stats
           (reep_id, season, league, source, wins, draws, losses, goals_for, goals_against, xg, xga, ppda)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("reep_t1", "2024-2025", "Premier League", "understat", 25, 8, 5, 80, 35, 78.5, 33.2, 8.5),
    )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/team/reep_t1/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["wins"] == 25
    assert data[0]["xg"] == 78.5


def test_get_team_squad():
    conn = _setup_test_db()
    conn.execute("INSERT INTO teams (reep_id, name) VALUES (?, ?)", ("reep_t1", "Arsenal"))
    conn.execute(
        "INSERT INTO people (reep_id, type, name, position, nationality) VALUES (?, ?, ?, ?, ?)",
        ("reep_p1", "player", "Bukayo Saka", "right winger", "England"),
    )
    conn.execute(
        "INSERT INTO squad_membership (reep_id, team_reep_id, season, league) VALUES (?, ?, ?, ?)",
        ("reep_p1", "reep_t1", "2024-2025", "Premier League"),
    )
    conn.execute(
        """INSERT INTO player_season_stats
           (reep_id, season, league, source, minutes_played, goals, assists, xg)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("reep_p1", "2024-2025", "Premier League", "fbref", 2500, 16, 9, 12.3),
    )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/team/reep_t1/squad?season=2024-2025")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Bukayo Saka"
    assert data[0]["goals"] == 16
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_api_teams.py -v`
Expected: 4 tests PASS

- [ ] **Step 4: Run ruff + commit**

```bash
uv run ruff check api/routers/teams.py tests/test_api_teams.py && uv run ruff format api/routers/teams.py tests/test_api_teams.py
git add api/routers/teams.py tests/test_api_teams.py
git commit -m "feat: team profile, stats, and squad endpoints"
```

---

### Task 7: Compare Endpoints

**Files:**
- Modify: `api/routers/compare.py`
- Create: `tests/test_api_compare.py`

- [ ] **Step 1: Implement compare router**

Replace the stub in `api/routers/compare.py`:

```python
from fastapi import APIRouter, Query

from api.deps import get_db
from api.models import PlayerSeasonStats, TeamSeasonStats
from api.queries import GET_PLAYER_STATS, GET_TEAM_STATS

router = APIRouter()


@router.get("/compare/players")
def compare_players(ids: str = Query(description="Comma-separated reep_ids")):
    conn = get_db()
    reep_ids = [id.strip() for id in ids.split(",")]

    result = {}
    for reep_id in reep_ids[:4]:  # Max 4 players
        rows = conn.execute(GET_PLAYER_STATS, (reep_id,)).fetchall()
        player = conn.execute(
            "SELECT name FROM people WHERE reep_id = ?", (reep_id,)
        ).fetchone()
        name = player["name"] if player else reep_id
        result[reep_id] = {
            "name": name,
            "seasons": [PlayerSeasonStats(**dict(row)).model_dump() for row in rows],
        }

    return result


@router.get("/compare/teams")
def compare_teams(ids: str = Query(description="Comma-separated reep_ids")):
    conn = get_db()
    reep_ids = [id.strip() for id in ids.split(",")]

    result = {}
    for reep_id in reep_ids[:2]:  # Max 2 teams
        rows = conn.execute(GET_TEAM_STATS, (reep_id,)).fetchall()
        team = conn.execute(
            "SELECT name FROM teams WHERE reep_id = ?", (reep_id,)
        ).fetchone()
        name = team["name"] if team else reep_id
        result[reep_id] = {
            "name": name,
            "seasons": [TeamSeasonStats(**dict(row)).model_dump() for row in rows],
        }

    return result
```

- [ ] **Step 2: Write tests**

Create `tests/test_api_compare.py`:

```python
from fastapi.testclient import TestClient

from api.app import app
from api.deps import override_db


def _setup_test_db():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from pipeline.db import init_schema
    init_schema(conn)
    override_db(conn)
    return conn


def test_compare_players():
    conn = _setup_test_db()
    for pid, name, goals in [("reep_p1", "Cole Palmer", 22), ("reep_p2", "Bukayo Saka", 16)]:
        conn.execute(
            "INSERT INTO people (reep_id, type, name) VALUES (?, ?, ?)",
            (pid, "player", name),
        )
        conn.execute(
            """INSERT INTO player_season_stats
               (reep_id, season, league, source, goals) VALUES (?, ?, ?, ?, ?)""",
            (pid, "2024-2025", "Premier League", "fbref", goals),
        )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/compare/players?ids=reep_p1,reep_p2")
    assert resp.status_code == 200
    data = resp.json()
    assert "reep_p1" in data
    assert "reep_p2" in data
    assert data["reep_p1"]["name"] == "Cole Palmer"
    assert data["reep_p2"]["name"] == "Bukayo Saka"


def test_compare_teams():
    conn = _setup_test_db()
    for tid, name, wins in [("reep_t1", "Arsenal", 25), ("reep_t2", "Chelsea", 20)]:
        conn.execute(
            "INSERT INTO teams (reep_id, name) VALUES (?, ?)",
            (tid, name),
        )
        conn.execute(
            """INSERT INTO team_season_stats
               (reep_id, season, league, source, wins) VALUES (?, ?, ?, ?, ?)""",
            (tid, "2024-2025", "Premier League", "understat", wins),
        )
    conn.commit()

    client = TestClient(app)
    resp = client.get("/api/compare/teams?ids=reep_t1,reep_t2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["reep_t1"]["name"] == "Arsenal"
    assert data["reep_t2"]["name"] == "Chelsea"
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_api_compare.py -v`
Expected: 2 tests PASS

- [ ] **Step 4: Run ruff + commit**

```bash
uv run ruff check api/routers/compare.py tests/test_api_compare.py && uv run ruff format api/routers/compare.py tests/test_api_compare.py
git add api/routers/compare.py tests/test_api_compare.py
git commit -m "feat: player and team comparison endpoints"
```

---

### Task 8: Explore Scatter Endpoint

**Files:**
- Modify: `api/routers/explore.py`
- Create: `tests/test_api_explore.py`

- [ ] **Step 1: Implement explore router**

Replace the stub in `api/routers/explore.py`:

```python
from fastapi import APIRouter, HTTPException, Query

from api.deps import get_db
from api.models import ScatterPoint

router = APIRouter()

ALLOWED_STATS = {
    "goals_per90", "xg_per90", "assists_per90", "xa_per90",
    "shots_per90", "key_passes_per90",
    "progressive_passes_per90", "progressive_carries_per90",
    "tackles_per90", "interceptions_per90", "pressures_per90", "take_ons_per90",
}


@router.get("/explore/scatter", response_model=list[ScatterPoint])
def scatter(
    x: str = Query(description="Per-90 stat for X axis"),
    y: str = Query(description="Per-90 stat for Y axis"),
    league: str | None = Query(default=None),
    position: str | None = Query(default=None),
):
    if x not in ALLOWED_STATS or y not in ALLOWED_STATS:
        raise HTTPException(
            status_code=400,
            detail=f"Stats must be one of: {', '.join(sorted(ALLOWED_STATS))}",
        )

    conn = get_db()

    # Build query with safe column names (validated against allowlist above)
    sql = f"""
        SELECT p90.reep_id, pe.name, pe.position, p90.league,
               p90.{x} as x_value, p90.{y} as y_value
        FROM player_per90 p90
        JOIN people pe ON p90.reep_id = pe.reep_id
        WHERE p90.{x} IS NOT NULL AND p90.{y} IS NOT NULL
    """
    params: list = []

    if league:
        sql += " AND p90.league = ?"
        params.append(league)

    if position:
        sql += " AND p90.position_group = ?"
        params.append(position)

    sql += " ORDER BY p90.reep_id LIMIT 500"

    rows = conn.execute(sql, params).fetchall()
    return [ScatterPoint(**dict(row)) for row in rows]
```

- [ ] **Step 2: Write tests**

Create `tests/test_api_explore.py`:

```python
from fastapi.testclient import TestClient

from api.app import app
from api.deps import override_db


def _setup_test_db():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from pipeline.db import init_schema
    init_schema(conn)
    override_db(conn)
    return conn


def _seed_per90(conn):
    conn.execute(
        "INSERT INTO people (reep_id, type, name, position) VALUES (?, ?, ?, ?)",
        ("reep_p1", "player", "Cole Palmer", "attacking midfielder"),
    )
    conn.execute(
        """INSERT INTO player_per90
           (reep_id, season, league, position_group, minutes_played,
            goals_per90, xg_per90, assists_per90, xa_per90,
            shots_per90, key_passes_per90, progressive_passes_per90, progressive_carries_per90,
            tackles_per90, interceptions_per90, pressures_per90, take_ons_per90,
            goals_pctile, xg_pctile, assists_pctile, xa_pctile,
            shots_pctile, key_passes_pctile, progressive_passes_pctile, progressive_carries_pctile,
            tackles_pctile, interceptions_pctile, pressures_pctile, take_ons_pctile)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("reep_p1", "2024-2025", "Premier League", "MF", 2700,
         0.73, 0.62, 0.37, 0.33, 2.67, 1.67, 2.33, 1.83, 0.67, 0.5, 5.0, 1.33,
         95, 90, 88, 85, 92, 80, 78, 75, 30, 25, 40, 70),
    )
    conn.commit()


def test_scatter_basic():
    conn = _setup_test_db()
    _seed_per90(conn)

    client = TestClient(app)
    resp = client.get("/api/explore/scatter?x=goals_per90&y=xg_per90")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Cole Palmer"
    assert data[0]["x_value"] == 0.73
    assert data[0]["y_value"] == 0.62


def test_scatter_filter_by_league():
    conn = _setup_test_db()
    _seed_per90(conn)

    client = TestClient(app)
    resp = client.get("/api/explore/scatter?x=goals_per90&y=xg_per90&league=La Liga")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 0  # Palmer is in Premier League


def test_scatter_invalid_stat():
    _setup_test_db()
    client = TestClient(app)
    resp = client.get("/api/explore/scatter?x=goals_per90&y=invalid_stat")
    assert resp.status_code == 400
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_api_explore.py -v`
Expected: 3 tests PASS

- [ ] **Step 4: Run ruff + commit**

```bash
uv run ruff check api/routers/explore.py tests/test_api_explore.py && uv run ruff format api/routers/explore.py tests/test_api_explore.py
git add api/routers/explore.py tests/test_api_explore.py
git commit -m "feat: scatter plot explore endpoint with stat validation"
```

---

### Task 9: Run All Tests + Final Verification

- [ ] **Step 1: Run the full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests pass (pipeline tests from Plan 1 + all new API tests)

- [ ] **Step 2: Run ruff on everything**

Run: `uv run ruff check . && uv run ruff format .`

- [ ] **Step 3: Test the server starts**

Run: `uv run uvicorn api.app:app --port 8000 &`
Then: `curl http://localhost:8000/api/health`
Expected: JSON response with health data
Kill the server after.

- [ ] **Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: test suite and lint adjustments"
```

---

## Summary

| Task | What it builds | Tests |
|------|---------------|-------|
| 1 | FastAPI deps in pyproject.toml | — |
| 2 | Pydantic models + SQL queries | — |
| 3 | App setup, health endpoint, DB deps | 2 |
| 4 | Search endpoint | 4 |
| 5 | Player endpoints (profile, stats, shots, radar) | 5 |
| 6 | Team endpoints (profile, stats, squad) | 4 |
| 7 | Compare endpoints (players, teams) | 2 |
| 8 | Explore scatter endpoint | 3 |
| 9 | Full test run + server verification | all |

**Deferred to Plan 5 (ML Features):**
- Player similarity endpoint
- Player-team fit endpoint
- Team style profile endpoint
- Team gap analysis endpoint
- UMAP cluster visualization endpoint

**After this plan:** The API serves all data the frontend needs for player profiles, team profiles, search, comparisons, and scatter plots. Plan 3 (Frontend — Player Module) can consume this API.
