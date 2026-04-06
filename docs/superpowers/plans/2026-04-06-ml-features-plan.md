# ML Features Implementation Plan (Plan 5 of 5)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ML-powered features: player similarity engine, player clustering (UMAP), player-team fit analysis, team style profiles, and positional gap analysis. Covers the pipeline compute stage, API endpoints, and frontend components.

**Architecture:** Pipeline compute stage generates embeddings (numpy arrays stored as BLOBs) and team profiles. API endpoints serve precomputed results. Frontend adds similar players tab, fit analysis widget, team style radar, and gap analysis to existing pages.

**Tech Stack:** scikit-learn, umap-learn, numpy (pipeline), FastAPI (API), Recharts (frontend)

---

## Scope

**Pipeline (compute):**
- Player embeddings from per-90 stat vectors (MinMaxScaler + cosine similarity)
- KMeans clustering with human-readable labels
- UMAP 2D projection for visualization
- Team style profiles (possession, pressing, directness scores)

**API (5 new endpoints):**
- `GET /api/player/{reep_id}/similar?n=10`
- `GET /api/player/{reep_id}/fit?team={reep_id}`
- `GET /api/team/{reep_id}/profile?season={season}`
- `GET /api/team/{reep_id}/gaps?season={season}`
- `GET /api/explore/clusters?season={season}`

**Frontend (4 new components + page updates):**
- Similar players list on player profile
- Player-team fit widget on player profile
- Team style radar on team profile
- Gap analysis on team profile
- Cluster map on explore page

## File Structure

```
pitch-intel/
├── pipeline/
│   └── stages/
│       └── ml.py                    # Embeddings, clustering, UMAP, team profiles
├── api/
│   ├── models.py                    # Add ML response models
│   ├── queries.py                   # Add ML queries
│   └── routers/
│       ├── players.py               # Add /similar and /fit endpoints
│       ├── teams.py                 # Add /profile and /gaps endpoints
│       └── explore.py               # Add /clusters endpoint
├── tests/
│   ├── test_ml.py                   # ML compute tests
│   └── test_api_ml.py              # ML endpoint tests
└── web/
    ├── lib/
    │   └── api.ts                   # Add ML types and functions
    ├── components/
    │   ├── similar-players.tsx      # Similar players list
    │   ├── fit-analysis.tsx         # Player-team fit widget
    │   ├── team-style-radar.tsx     # Team style radar chart
    │   ├── gap-analysis.tsx         # Positional gap analysis
    │   └── cluster-map.tsx          # UMAP scatter plot
    └── app/
        ├── player/[reepId]/page.tsx # Add similar + fit sections
        ├── team/[reepId]/page.tsx   # Add style + gaps sections
        └── explore/page.tsx         # Add cluster tab
```

---

### Task 1: Add ML Dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add scikit-learn, umap-learn, numpy**

Add to `dependencies` in `pyproject.toml`:
```toml
    "scikit-learn>=1.5",
    "umap-learn>=0.5",
    "numpy>=2.0",
```

- [ ] **Step 2: Install**

Run: `uv sync`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add scikit-learn, umap-learn, numpy dependencies"
```

---

### Task 2: ML Compute Stage — Embeddings + Clustering

**Files:**
- Create: `pipeline/stages/ml.py`
- Create: `tests/test_ml.py`

- [ ] **Step 1: Write tests**

Create `tests/test_ml.py`:

```python
import numpy as np
import polars as pl

from pipeline.stages.ml import (
    compute_embeddings,
    compute_clusters,
    compute_team_profiles,
    find_similar_players,
)


def test_compute_embeddings():
    df = pl.DataFrame({
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
    })

    result = compute_embeddings(df)

    assert len(result) == 3
    assert "reep_id" in result.columns
    assert "embedding" in result.columns
    # Embedding should be bytes (serialized numpy array)
    assert isinstance(result["embedding"][0], bytes)
    emb = np.frombuffer(result["embedding"][0], dtype=np.float32)
    assert len(emb) == 12  # 12 per-90 stats


def test_find_similar_players():
    # Create 5 players — p1 and p3 should be most similar (high goals, low defense)
    df = pl.DataFrame({
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
    })

    embeddings = compute_embeddings(df)
    similar = find_similar_players(embeddings, "p1", n=3)

    assert len(similar) == 3
    # p3 should be most similar to p1
    assert similar[0]["reep_id"] == "p3"
    assert 0 < similar[0]["similarity"] <= 1.0


def test_compute_clusters():
    df = pl.DataFrame({
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
    })

    embeddings = compute_embeddings(df)
    clustered = compute_clusters(embeddings, n_clusters=4)

    assert "cluster_id" in clustered.columns
    assert "cluster_label" in clustered.columns
    assert "umap_x" in clustered.columns
    assert "umap_y" in clustered.columns
    assert len(clustered) == 20


def test_compute_team_profiles(db):
    # Seed team + squad + stats
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
        ("p1", "2024-2025", "Premier League", "understat", 2500, 16, 12, 13.2, 1100, 1380, 82, 210, 68),
    )
    db.execute(
        """INSERT INTO player_season_stats
           (reep_id, season, league, source, minutes_played, goals, assists, xg,
            passes_completed, passes_attempted, progressive_passes, pressures, pressure_successes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("p2", "2024-2025", "Premier League", "understat", 2800, 5, 7, 4.2, 1900, 2150, 105, 265, 88),
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
```

- [ ] **Step 2: Implement ML compute module**

Create `pipeline/stages/ml.py`:

```python
import sqlite3
from datetime import date

import numpy as np
import polars as pl
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

from pipeline.stages.compute import PER90_OUTPUT_NAMES

CLUSTER_LABELS = {
    0: "Goal Scorer",
    1: "Deep Defender",
    2: "Creative Playmaker",
    3: "Box-to-Box",
    4: "Pressing Forward",
    5: "Ball-Playing Defender",
    6: "Wide Attacker",
    7: "Defensive Midfielder",
}


def compute_embeddings(per90_df: pl.DataFrame) -> pl.DataFrame:
    """Compute normalized embeddings from per-90 stats.

    Input: DataFrame with reep_id + per-90 stat columns.
    Output: DataFrame with reep_id + embedding (bytes) columns.
    """
    stat_cols = [c for c in PER90_OUTPUT_NAMES if c in per90_df.columns]
    matrix = per90_df.select(stat_cols).fill_null(0).to_numpy().astype(np.float32)

    scaler = MinMaxScaler()
    normalized = scaler.fit_transform(matrix).astype(np.float32)

    reep_ids = per90_df["reep_id"].to_list()
    embeddings = [row.tobytes() for row in normalized]

    return pl.DataFrame({
        "reep_id": reep_ids,
        "embedding": embeddings,
    })


def find_similar_players(
    embeddings_df: pl.DataFrame,
    target_reep_id: str,
    n: int = 10,
) -> list[dict]:
    """Find the N most similar players to a target player.

    Returns list of {reep_id, similarity} dicts sorted by similarity desc.
    """
    reep_ids = embeddings_df["reep_id"].to_list()
    raw_embeddings = embeddings_df["embedding"].to_list()

    vectors = np.array(
        [np.frombuffer(e, dtype=np.float32) for e in raw_embeddings]
    )

    if target_reep_id not in reep_ids:
        return []

    target_idx = reep_ids.index(target_reep_id)
    target_vec = vectors[target_idx].reshape(1, -1)

    similarities = cosine_similarity(target_vec, vectors)[0]

    # Sort by similarity, exclude self
    indices = np.argsort(similarities)[::-1]
    results = []
    for idx in indices:
        if reep_ids[idx] == target_reep_id:
            continue
        results.append({
            "reep_id": reep_ids[idx],
            "similarity": round(float(similarities[idx]), 4),
        })
        if len(results) >= n:
            break

    return results


def compute_clusters(
    embeddings_df: pl.DataFrame,
    n_clusters: int = 8,
) -> pl.DataFrame:
    """Cluster players and compute UMAP 2D projections.

    Returns DataFrame with reep_id, cluster_id, cluster_label, umap_x, umap_y.
    """
    reep_ids = embeddings_df["reep_id"].to_list()
    raw_embeddings = embeddings_df["embedding"].to_list()

    vectors = np.array(
        [np.frombuffer(e, dtype=np.float32) for e in raw_embeddings]
    )

    # Adjust n_clusters if we have fewer samples
    actual_clusters = min(n_clusters, len(vectors))

    # KMeans clustering
    kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
    cluster_ids = kmeans.fit_predict(vectors)

    # UMAP 2D projection
    try:
        import umap

        reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=min(15, len(vectors) - 1))
        coords = reducer.fit_transform(vectors)
        umap_x = coords[:, 0].tolist()
        umap_y = coords[:, 1].tolist()
    except Exception:
        # Fallback to PCA if UMAP fails (e.g., too few samples)
        from sklearn.decomposition import PCA

        pca = PCA(n_components=2, random_state=42)
        coords = pca.fit_transform(vectors)
        umap_x = coords[:, 0].tolist()
        umap_y = coords[:, 1].tolist()

    labels = [CLUSTER_LABELS.get(int(c), f"Cluster {c}") for c in cluster_ids]

    return pl.DataFrame({
        "reep_id": reep_ids,
        "cluster_id": [int(c) for c in cluster_ids],
        "cluster_label": labels,
        "umap_x": umap_x,
        "umap_y": umap_y,
    })


def _calculate_age(dob: str) -> int | None:
    """Calculate age from date of birth string."""
    try:
        birth = date.fromisoformat(dob)
        today = date.today()
        age = today.year - birth.year
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        return age
    except (ValueError, TypeError):
        return None


def compute_team_profiles(
    conn: sqlite3.Connection,
    season: str,
) -> list[dict]:
    """Compute team style profiles from squad and team stats.

    Returns list of profile dicts ready for upserting into team_profiles.
    """
    teams_with_squads = conn.execute(
        """SELECT DISTINCT sm.team_reep_id, sm.league
           FROM squad_membership sm
           WHERE sm.season = ?""",
        (season,),
    ).fetchall()

    profiles = []
    for row in teams_with_squads:
        team_id, league = row[0], row[1]

        # Get squad members with stats
        members = conn.execute(
            """SELECT p.reep_id, p.position, p.date_of_birth, p.nationality,
                      s.minutes_played
               FROM squad_membership sm
               JOIN people p ON sm.reep_id = p.reep_id
               LEFT JOIN player_season_stats s
                   ON sm.reep_id = s.reep_id AND sm.season = s.season AND sm.league = s.league
               WHERE sm.team_reep_id = ? AND sm.season = ?""",
            (team_id, season),
        ).fetchall()

        if not members:
            continue

        # Squad composition
        squad_size = len(members)
        ages = []
        foreign_count = 0
        pos_counts = {"FW": 0, "MF": 0, "DF": 0, "GK": 0}
        position_map = {
            "goalkeeper": "GK", "centre-back": "DF", "left-back": "DF",
            "right-back": "DF", "defensive midfield": "MF", "central midfield": "MF",
            "attacking midfield": "MF", "left midfield": "MF", "right midfield": "MF",
            "left winger": "FW", "right winger": "FW", "centre-forward": "FW",
            "second striker": "FW",
        }

        for m in members:
            if m[2]:  # date_of_birth
                age = _calculate_age(m[2])
                if age:
                    ages.append(age)
            if m[1]:  # position
                pg = position_map.get(m[1], "MF")
                mins = m[4] or 0
                if mins >= 900:
                    pos_counts[pg] += 1

        # Team stats for style scores
        team_stats = conn.execute(
            """SELECT ppda, xg, xga
               FROM team_season_stats
               WHERE reep_id = ? AND season = ? AND league = ?
               LIMIT 1""",
            (team_id, season, league),
        ).fetchone()

        # Compute style scores (0-100 scale, normalized later)
        ppda = team_stats[0] if team_stats and team_stats[0] else 10.0
        pressing_score = max(0, min(100, (15 - ppda) / 10 * 100))

        # Possession proxy from pass completion
        squad_stats = conn.execute(
            """SELECT SUM(passes_completed), SUM(passes_attempted), SUM(progressive_passes)
               FROM player_season_stats
               WHERE reep_id IN (
                   SELECT reep_id FROM squad_membership WHERE team_reep_id = ? AND season = ?
               ) AND season = ?""",
            (team_id, season, season),
        ).fetchone()

        pass_pct = (squad_stats[0] / squad_stats[1] * 100) if squad_stats and squad_stats[1] else 80
        possession_score = max(0, min(100, (pass_pct - 70) / 20 * 100))

        prog_passes = squad_stats[2] if squad_stats and squad_stats[2] else 0
        directness_score = max(0, min(100, prog_passes / 10))

        profiles.append({
            "reep_id": team_id,
            "season": season,
            "league": league,
            "possession_score": round(possession_score, 1),
            "pressing_score": round(pressing_score, 1),
            "directness_score": round(directness_score, 1),
            "set_piece_reliance": 0.0,  # Would need set piece xG data
            "avg_age": round(sum(ages) / len(ages), 1) if ages else None,
            "squad_size": squad_size,
            "foreign_player_pct": 0.0,  # Would need nationality matching
            "fw_depth": pos_counts["FW"],
            "mf_depth": pos_counts["MF"],
            "df_depth": pos_counts["DF"],
            "gk_depth": pos_counts["GK"],
        })

    return profiles
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_ml.py -v`
Expected: 4 tests PASS

- [ ] **Step 4: Run ruff + commit**

```bash
uv run ruff check pipeline/stages/ml.py tests/test_ml.py && uv run ruff format pipeline/stages/ml.py tests/test_ml.py
git add pipeline/stages/ml.py tests/test_ml.py
git commit -m "feat: ML compute — embeddings, similarity, clustering, team profiles"
```

---

### Task 3: ML Pipeline Integration

**Files:**
- Modify: `pipeline/cli.py`
- Modify: `pipeline/db.py`

- [ ] **Step 1: Add upsert functions for embeddings and team profiles to db.py**

Append to `pipeline/db.py`:

```python
def upsert_embeddings(conn: sqlite3.Connection, df: pl.DataFrame) -> int:
    """Upsert player embeddings. Returns row count."""
    rows = df.to_dicts()
    for row in rows:
        conn.execute(
            """INSERT INTO player_embeddings (reep_id, season, embedding, cluster_id, cluster_label)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(reep_id) DO UPDATE SET
               season = excluded.season, embedding = excluded.embedding,
               cluster_id = excluded.cluster_id, cluster_label = excluded.cluster_label,
               computed_at = datetime('now')""",
            (row["reep_id"], row.get("season", ""), row["embedding"],
             row.get("cluster_id"), row.get("cluster_label")),
        )
    conn.commit()
    return len(rows)


def upsert_team_profiles(conn: sqlite3.Connection, profiles: list[dict]) -> int:
    """Upsert team profiles. Returns row count."""
    for p in profiles:
        conn.execute(
            """INSERT INTO team_profiles
               (reep_id, season, league, possession_score, pressing_score,
                directness_score, set_piece_reliance, avg_age, squad_size,
                foreign_player_pct, fw_depth, mf_depth, df_depth, gk_depth)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(reep_id, season, league) DO UPDATE SET
               possession_score = excluded.possession_score,
               pressing_score = excluded.pressing_score,
               directness_score = excluded.directness_score,
               avg_age = excluded.avg_age, squad_size = excluded.squad_size,
               fw_depth = excluded.fw_depth, mf_depth = excluded.mf_depth,
               df_depth = excluded.df_depth, gk_depth = excluded.gk_depth,
               computed_at = datetime('now')""",
            tuple(p[k] for k in [
                "reep_id", "season", "league", "possession_score", "pressing_score",
                "directness_score", "set_piece_reliance", "avg_age", "squad_size",
                "foreign_player_pct", "fw_depth", "mf_depth", "df_depth", "gk_depth",
            ]),
        )
    conn.commit()
    return len(profiles)
```

- [ ] **Step 2: Add ML stage to CLI run command**

In `pipeline/cli.py`, after the existing Stage 4 (compute per-90), add a new Stage 5 block before the "Log completion" section:

```python
    # Stage 5: ML features
    click.echo("Stage 5: Computing ML features...")
    try:
        from pipeline.stages.ml import compute_embeddings, compute_clusters, compute_team_profiles
        from pipeline.db import upsert_embeddings, upsert_team_profiles

        # Load per-90 data
        per90_rows = conn.execute(
            "SELECT * FROM player_per90 WHERE season = ?", (season,)
        ).fetchall()
        if per90_rows:
            per90_cols = [desc[0] for desc in conn.execute("SELECT * FROM player_per90 LIMIT 0").description]
            per90_df = pl.DataFrame([dict(zip(per90_cols, row)) for row in per90_rows])

            # Embeddings
            emb_df = compute_embeddings(per90_df)
            emb_df = emb_df.with_columns(pl.lit(season).alias("season"))

            # Clustering
            clustered = compute_clusters(emb_df)
            emb_with_clusters = emb_df.join(
                clustered.select("reep_id", "cluster_id", "cluster_label"),
                on="reep_id",
            )
            upsert_embeddings(conn, emb_with_clusters)
            click.echo(f"  {len(emb_with_clusters)} player embeddings computed.")

            # Store UMAP coords in a temp way for the API (we'll query embeddings table)
            # The API will recompute UMAP from stored embeddings on demand

        # Team profiles
        profiles = compute_team_profiles(conn, season)
        if profiles:
            upsert_team_profiles(conn, profiles)
            click.echo(f"  {len(profiles)} team profiles computed.")
        else:
            click.echo("  No team profiles to compute (no squad data).")
    except Exception as e:
        errors.append(f"ML features: {e}")
        click.echo(f"  ERROR: {e}")
```

- [ ] **Step 3: Run ruff + commit**

```bash
uv run ruff check pipeline/ && uv run ruff format pipeline/
git add pipeline/cli.py pipeline/db.py
git commit -m "feat: ML pipeline integration — embeddings, clusters, team profiles"
```

---

### Task 4: ML API Endpoints

**Files:**
- Modify: `api/models.py`
- Modify: `api/queries.py`
- Modify: `api/routers/players.py`
- Modify: `api/routers/teams.py`
- Modify: `api/routers/explore.py`
- Create: `tests/test_api_ml.py`

- [ ] **Step 1: Add ML models to api/models.py**

Append to `api/models.py`:

```python
class SimilarPlayer(BaseModel):
    reep_id: str
    name: str
    position: str | None = None
    similarity: float


class FitAnalysis(BaseModel):
    player_name: str
    team_name: str
    position_rank: int | None = None
    position_total: int | None = None
    style_notes: list[str]


class TeamStyleProfile(BaseModel):
    reep_id: str
    season: str
    league: str
    possession_score: float | None = None
    pressing_score: float | None = None
    directness_score: float | None = None
    avg_age: float | None = None
    squad_size: int | None = None
    fw_depth: int | None = None
    mf_depth: int | None = None
    df_depth: int | None = None
    gk_depth: int | None = None


class GapAnalysisItem(BaseModel):
    position_group: str
    depth: int
    avg_age: float | None = None
    risk: str  # "thin", "aging", "ok"


class ClusterPoint(BaseModel):
    reep_id: str
    name: str
    position: str | None = None
    cluster_id: int
    cluster_label: str
    umap_x: float
    umap_y: float
```

- [ ] **Step 2: Add ML queries to api/queries.py**

Append to `api/queries.py`:

```python
GET_PLAYER_EMBEDDING = """
    SELECT reep_id, embedding FROM player_embeddings WHERE reep_id = ?
"""

GET_ALL_EMBEDDINGS = """
    SELECT pe.reep_id, pe.embedding, p.name, p.position
    FROM player_embeddings pe
    JOIN people p ON pe.reep_id = p.reep_id
"""

GET_TEAM_PROFILE = """
    SELECT reep_id, season, league, possession_score, pressing_score,
           directness_score, avg_age, squad_size, fw_depth, mf_depth, df_depth, gk_depth
    FROM team_profiles
    WHERE reep_id = ?
    ORDER BY season DESC
    LIMIT 1
"""

GET_TEAM_PROFILE_BY_SEASON = """
    SELECT reep_id, season, league, possession_score, pressing_score,
           directness_score, avg_age, squad_size, fw_depth, mf_depth, df_depth, gk_depth
    FROM team_profiles
    WHERE reep_id = ? AND season = ?
    LIMIT 1
"""

GET_CLUSTER_DATA = """
    SELECT pe.reep_id, p.name, p.position, pe.cluster_id, pe.cluster_label
    FROM player_embeddings pe
    JOIN people p ON pe.reep_id = p.reep_id
    WHERE pe.season = ?
"""
```

- [ ] **Step 3: Add /similar endpoint to players.py**

Add to `api/routers/players.py`:

```python
@router.get("/player/{reep_id}/similar", response_model=list)
def get_similar_players(reep_id: str, n: int = Query(default=10, le=50)):
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity as cos_sim

    conn = get_db()

    # Get target embedding
    target = conn.execute(
        "SELECT embedding FROM player_embeddings WHERE reep_id = ?", (reep_id,)
    ).fetchone()
    if not target:
        return []

    target_vec = np.frombuffer(target["embedding"], dtype=np.float32).reshape(1, -1)

    # Get all embeddings
    all_rows = conn.execute(
        """SELECT pe.reep_id, pe.embedding, p.name, p.position
           FROM player_embeddings pe
           JOIN people p ON pe.reep_id = p.reep_id"""
    ).fetchall()

    reep_ids = [r["reep_id"] for r in all_rows]
    names = {r["reep_id"]: r["name"] for r in all_rows}
    positions = {r["reep_id"]: r["position"] for r in all_rows}
    vectors = np.array([np.frombuffer(r["embedding"], dtype=np.float32) for r in all_rows])

    similarities = cos_sim(target_vec, vectors)[0]
    indices = np.argsort(similarities)[::-1]

    results = []
    for idx in indices:
        rid = reep_ids[idx]
        if rid == reep_id:
            continue
        results.append({
            "reep_id": rid,
            "name": names[rid],
            "position": positions[rid],
            "similarity": round(float(similarities[idx]), 4),
        })
        if len(results) >= n:
            break

    return results


@router.get("/player/{reep_id}/fit")
def get_player_fit(reep_id: str, team: str = Query()):
    conn = get_db()

    player = conn.execute("SELECT name, position FROM people WHERE reep_id = ?", (reep_id,)).fetchone()
    team_row = conn.execute("SELECT name FROM teams WHERE reep_id = ?", (team,)).fetchone()

    if not player or not team_row:
        raise HTTPException(status_code=404, detail="Player or team not found")

    # Get player's per-90 stats
    player_per90 = conn.execute(
        "SELECT * FROM player_per90 WHERE reep_id = ? ORDER BY season DESC LIMIT 1", (reep_id,)
    ).fetchone()

    # Get team squad's per-90 stats at same position
    position_map = {
        "goalkeeper": "GK", "centre-back": "DF", "left-back": "DF", "right-back": "DF",
        "defensive midfield": "MF", "central midfield": "MF", "attacking midfield": "MF",
        "left midfield": "MF", "right midfield": "MF", "left winger": "FW",
        "right winger": "FW", "centre-forward": "FW", "second striker": "FW",
    }
    pos_group = position_map.get(player["position"], "MF") if player["position"] else "MF"

    squad_per90 = conn.execute(
        """SELECT p90.reep_id, p90.goals_per90, p90.xg_per90, p90.assists_per90
           FROM player_per90 p90
           JOIN squad_membership sm ON p90.reep_id = sm.reep_id
           WHERE sm.team_reep_id = ? AND p90.position_group = ?
           ORDER BY p90.minutes_played DESC""",
        (team, pos_group),
    ).fetchall()

    position_rank = None
    position_total = len(squad_per90)
    if player_per90 and squad_per90:
        player_xg = player_per90["xg_per90"] or 0
        rank = sum(1 for s in squad_per90 if (s["xg_per90"] or 0) > player_xg) + 1
        position_rank = rank

    # Style notes
    notes = []
    team_profile = conn.execute(
        "SELECT * FROM team_profiles WHERE reep_id = ? ORDER BY season DESC LIMIT 1", (team,)
    ).fetchone()
    if team_profile:
        if team_profile["pressing_score"] and team_profile["pressing_score"] > 60:
            notes.append("Team presses high — player needs good work rate")
        if team_profile["possession_score"] and team_profile["possession_score"] > 60:
            notes.append("Possession-heavy side — passing ability valued")

    return {
        "player_name": player["name"],
        "team_name": team_row["name"],
        "position_rank": position_rank,
        "position_total": position_total,
        "style_notes": notes,
    }
```

Add these imports at the top of `api/routers/players.py` if not present:
```python
import numpy as np
```

- [ ] **Step 4: Add /profile and /gaps to teams.py**

Add to `api/routers/teams.py`:

```python
@router.get("/team/{reep_id}/profile")
def get_team_profile(reep_id: str, season: str | None = Query(default=None)):
    conn = get_db()
    if season:
        row = conn.execute(
            """SELECT reep_id, season, league, possession_score, pressing_score,
                      directness_score, avg_age, squad_size, fw_depth, mf_depth, df_depth, gk_depth
               FROM team_profiles WHERE reep_id = ? AND season = ? LIMIT 1""",
            (reep_id, season),
        ).fetchone()
    else:
        row = conn.execute(
            """SELECT reep_id, season, league, possession_score, pressing_score,
                      directness_score, avg_age, squad_size, fw_depth, mf_depth, df_depth, gk_depth
               FROM team_profiles WHERE reep_id = ? ORDER BY season DESC LIMIT 1""",
            (reep_id,),
        ).fetchone()

    if not row:
        return None
    return dict(row)


@router.get("/team/{reep_id}/gaps")
def get_team_gaps(reep_id: str, season: str | None = Query(default=None)):
    conn = get_db()

    profile_query = (
        "SELECT * FROM team_profiles WHERE reep_id = ? AND season = ? LIMIT 1"
        if season
        else "SELECT * FROM team_profiles WHERE reep_id = ? ORDER BY season DESC LIMIT 1"
    )
    params = (reep_id, season) if season else (reep_id,)
    profile = conn.execute(profile_query, params).fetchone()

    if not profile:
        return []

    gaps = []
    for pos, key in [("FW", "fw_depth"), ("MF", "mf_depth"), ("DF", "df_depth"), ("GK", "gk_depth")]:
        depth = profile[key] or 0
        risk = "thin" if depth <= 1 else "ok"
        gaps.append({
            "position_group": pos,
            "depth": depth,
            "avg_age": None,  # Would need per-position age calc
            "risk": risk,
        })

    return gaps
```

- [ ] **Step 5: Add /clusters to explore.py**

Add to `api/routers/explore.py`:

```python
@router.get("/explore/clusters")
def get_clusters(season: str = Query(default="2024-2025")):
    import numpy as np

    conn = get_db()

    rows = conn.execute(
        """SELECT pe.reep_id, p.name, p.position, pe.cluster_id, pe.cluster_label, pe.embedding
           FROM player_embeddings pe
           JOIN people p ON pe.reep_id = p.reep_id
           WHERE pe.season = ?""",
        (season,),
    ).fetchall()

    if not rows:
        return []

    # Compute UMAP on the fly from stored embeddings
    vectors = np.array([np.frombuffer(r["embedding"], dtype=np.float32) for r in rows])

    try:
        import umap
        reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=min(15, len(vectors) - 1))
        coords = reducer.fit_transform(vectors)
    except Exception:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2, random_state=42)
        coords = pca.fit_transform(vectors)

    return [
        {
            "reep_id": r["reep_id"],
            "name": r["name"],
            "position": r["position"],
            "cluster_id": r["cluster_id"],
            "cluster_label": r["cluster_label"],
            "umap_x": round(float(coords[i][0]), 4),
            "umap_y": round(float(coords[i][1]), 4),
        }
        for i, r in enumerate(rows)
    ]
```

- [ ] **Step 6: Write API tests**

Create `tests/test_api_ml.py`:

```python
import numpy as np
from fastapi.testclient import TestClient

from api.app import app
from api.deps import override_db


def _setup_test_db():
    import sqlite3
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    from pipeline.db import init_schema
    init_schema(conn)
    override_db(conn)
    return conn


def _seed_ml_data(conn):
    conn.execute("INSERT INTO people (reep_id, type, name, position) VALUES (?, ?, ?, ?)",
                 ("p1", "player", "Cole Palmer", "attacking midfielder"))
    conn.execute("INSERT INTO people (reep_id, type, name, position) VALUES (?, ?, ?, ?)",
                 ("p2", "player", "Bukayo Saka", "right winger"))
    conn.execute("INSERT INTO teams (reep_id, name) VALUES (?, ?)", ("t1", "Arsenal"))

    # Embeddings
    emb1 = np.array([0.8, 0.7, 0.3, 0.2, 0.9, 0.5, 0.6, 0.7, 0.2, 0.1, 0.3, 0.8], dtype=np.float32)
    emb2 = np.array([0.6, 0.5, 0.4, 0.3, 0.7, 0.6, 0.5, 0.6, 0.3, 0.2, 0.4, 0.7], dtype=np.float32)
    conn.execute(
        "INSERT INTO player_embeddings (reep_id, season, embedding, cluster_id, cluster_label) VALUES (?, ?, ?, ?, ?)",
        ("p1", "2024-2025", emb1.tobytes(), 0, "Goal Scorer"))
    conn.execute(
        "INSERT INTO player_embeddings (reep_id, season, embedding, cluster_id, cluster_label) VALUES (?, ?, ?, ?, ?)",
        ("p2", "2024-2025", emb2.tobytes(), 0, "Goal Scorer"))

    # Team profile
    conn.execute(
        """INSERT INTO team_profiles (reep_id, season, league, possession_score, pressing_score,
           directness_score, avg_age, squad_size, fw_depth, mf_depth, df_depth, gk_depth)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("t1", "2024-2025", "Premier League", 72.0, 65.0, 45.0, 26.5, 25, 5, 8, 9, 3))
    conn.commit()


def test_similar_players():
    conn = _setup_test_db()
    _seed_ml_data(conn)
    client = TestClient(app)
    resp = client.get("/api/player/p1/similar?n=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["reep_id"] == "p2"
    assert data[0]["similarity"] > 0


def test_team_profile():
    conn = _setup_test_db()
    _seed_ml_data(conn)
    client = TestClient(app)
    resp = client.get("/api/team/t1/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["possession_score"] == 72.0
    assert data["pressing_score"] == 65.0


def test_team_gaps():
    conn = _setup_test_db()
    _seed_ml_data(conn)
    client = TestClient(app)
    resp = client.get("/api/team/t1/gaps")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
    assert any(g["position_group"] == "GK" and g["depth"] == 3 for g in data)


def test_clusters():
    conn = _setup_test_db()
    _seed_ml_data(conn)
    client = TestClient(app)
    resp = client.get("/api/explore/clusters?season=2024-2025")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert "umap_x" in data[0]
    assert "cluster_label" in data[0]
```

- [ ] **Step 7: Run all tests**

Run: `uv run pytest tests/test_ml.py tests/test_api_ml.py -v`

- [ ] **Step 8: Run ruff + commit**

```bash
uv run ruff check api/ tests/ && uv run ruff format api/ tests/
git add api/ tests/test_api_ml.py
git commit -m "feat: ML API endpoints — similar players, fit, team profile, gaps, clusters"
```

---

### Task 5: Frontend ML Components + Page Updates

**Files:**
- Modify: `web/lib/api.ts`
- Create: `web/components/similar-players.tsx`
- Create: `web/components/fit-analysis.tsx`
- Create: `web/components/team-style-radar.tsx`
- Create: `web/components/gap-analysis.tsx`
- Create: `web/components/cluster-map.tsx`
- Modify: `web/app/player/[reepId]/page.tsx`
- Modify: `web/app/team/[reepId]/page.tsx`
- Modify: `web/app/explore/page.tsx`

- [ ] **Step 1: Add ML types and functions to api.ts**

Append to `web/lib/api.ts`:

```typescript
export interface SimilarPlayer {
  reep_id: string;
  name: string;
  position?: string;
  similarity: number;
}

export interface FitAnalysis {
  player_name: string;
  team_name: string;
  position_rank?: number;
  position_total?: number;
  style_notes: string[];
}

export interface TeamStyleProfile {
  reep_id: string;
  season: string;
  league: string;
  possession_score?: number;
  pressing_score?: number;
  directness_score?: number;
  avg_age?: number;
  squad_size?: number;
  fw_depth?: number;
  mf_depth?: number;
  df_depth?: number;
  gk_depth?: number;
}

export interface GapAnalysisItem {
  position_group: string;
  depth: number;
  avg_age?: number;
  risk: string;
}

export interface ClusterPoint {
  reep_id: string;
  name: string;
  position?: string;
  cluster_id: number;
  cluster_label: string;
  umap_x: number;
  umap_y: number;
}

export async function getSimilarPlayers(reepId: string, n: number = 10): Promise<SimilarPlayer[]> {
  return fetchApi<SimilarPlayer[]>(`/player/${reepId}/similar?n=${n}`);
}

export async function getPlayerFit(reepId: string, teamId: string): Promise<FitAnalysis> {
  return fetchApi<FitAnalysis>(`/player/${reepId}/fit?team=${teamId}`);
}

export async function getTeamProfile(reepId: string, season?: string): Promise<TeamStyleProfile | null> {
  const params = season ? `?season=${season}` : "";
  return fetchApi<TeamStyleProfile | null>(`/team/${reepId}/profile${params}`);
}

export async function getTeamGaps(reepId: string, season?: string): Promise<GapAnalysisItem[]> {
  const params = season ? `?season=${season}` : "";
  return fetchApi<GapAnalysisItem[]>(`/team/${reepId}/gaps${params}`);
}

export async function getClusters(season: string): Promise<ClusterPoint[]> {
  return fetchApi<ClusterPoint[]>(`/explore/clusters?season=${season}`);
}
```

- [ ] **Step 2-6: Create the 5 frontend components**

Create `web/components/similar-players.tsx`, `web/components/fit-analysis.tsx`, `web/components/team-style-radar.tsx`, `web/components/gap-analysis.tsx`, `web/components/cluster-map.tsx` — these are client components using the API functions and Recharts for visualizations.

(The subagent implementing this task should create each component following the patterns established in Plans 3-4: client components with "use client" directive, dark theme Tailwind classes, Recharts for charts.)

- [ ] **Step 7: Update player profile page to include similar players + fit**

Add `getSimilarPlayers` call to the player page's `Promise.all`, render `<SimilarPlayers>` and `<FitAnalysis>` sections.

- [ ] **Step 8: Update team profile page to include style radar + gaps**

Add `getTeamProfile` and `getTeamGaps` calls, render `<TeamStyleRadar>` and `<GapAnalysis>` sections.

- [ ] **Step 9: Update explore page to include cluster tab**

Add a tab toggle between "Scatter" and "Clusters" views. The cluster view uses `<ClusterMap>`.

- [ ] **Step 10: Type check + build**

```bash
cd web && npx tsc --noEmit && pnpm build
```

- [ ] **Step 11: Commit**

```bash
git add web/
git commit -m "feat: ML frontend — similar players, fit, team style, gaps, clusters"
```

---

### Task 6: Run ML Pipeline + Full Verification

- [ ] **Step 1: Run ML pipeline on local DB**

```bash
uv run python -m pipeline.cli run --skip-identity --skip-fbref --skip-understat --season "2024-2025" --local-db local.db
```

This should compute embeddings, clusters, and team profiles from the existing per-90 data.

- [ ] **Step 2: Run full test suite**

```bash
uv run pytest tests/ -v
```

- [ ] **Step 3: Run ruff everywhere**

```bash
uv run ruff check . && uv run ruff format .
```

- [ ] **Step 4: Final commit + push**

```bash
git add -A && git commit -m "fix: final adjustments" && git push origin main
```

---

## Summary

| Task | What it builds | Tests |
|------|---------------|-------|
| 1 | ML dependencies (scikit-learn, umap-learn, numpy) | — |
| 2 | ML compute: embeddings, similarity, clustering, team profiles | 4 |
| 3 | ML pipeline integration (CLI + DB upserts) | — |
| 4 | ML API endpoints (similar, fit, profile, gaps, clusters) | 4 |
| 5 | ML frontend components + page updates | `tsc` + `pnpm build` |
| 6 | Full pipeline run + verification | all tests |

**After this plan:** Pitch Intel is feature-complete. All 5 plans implemented: data pipeline, REST API, player frontend, team frontend, and ML features.
