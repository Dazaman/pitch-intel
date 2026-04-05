# Pitch Intel — Design Spec

**Date:** 2026-04-06
**Status:** Approved
**Author:** Danial Azam

A football intelligence platform combining player analysis and team/squad analytics, powered by the Reep identity register. Built as a portfolio piece, practical tool, and open-source contribution.

---

## 1. Architecture Overview

Three-layer architecture:

```
┌─────────────────────────────────┐
│        React Frontend           │
│   (Next.js + Tailwind + Charts) │
└──────────────┬──────────────────┘
               │ REST API
┌──────────────▼──────────────────┐
│        Python Backend           │
│   (FastAPI + ML models)         │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│        Data Layer               │
│  Turso (libSQL)                 │
│  Reep API · FBref · Understat   │
└─────────────────────────────────┘
```

**Data flow:**

1. **Reep API** is the identity backbone — every search resolves a player/team to a Reep ID.
2. **FBref + Understat** provide actual stats, linked through Reep's cross-provider ID mappings.
3. **Turso** stores cached player/team profiles and computed features (similarity embeddings, squad compositions).
4. **FastAPI** serves the frontend and runs ML inference (similarity, clustering, fit scoring).
5. **Next.js frontend** renders search, profiles, radars, and squad views.

Data is not fetched on demand. A weekly pipeline pulls stats via Reep ID mappings, computes features, and stores them. The app reads from its own database.

## 2. Deployment

All free tier:

| Layer | Service |
|-------|---------|
| Frontend | Vercel (free tier) |
| Backend | Railway (free tier — 500 hrs/month, 512MB RAM) |
| Database | Turso (free tier — 9GB storage, 500M row reads/month) |
| Pipeline | GitHub Actions (weekly cron) |

Railway's free tier sleeps after 30 min of inactivity (cold starts ~5-10s). Acceptable for a portfolio project.

## 3. Data Pipeline

### 3.1 Data Sources

| Source | What We Get | Method | Rate Limit |
|--------|------------|--------|------------|
| **Reep API** | Player/team identity + cross-provider IDs | REST API (RapidAPI) | Per plan |
| **FBref** | Per-90 stats, season history, percentile ranks | `soccerdata` scraper | ~10 req/min (6s delay) |
| **Understat** | Shot-level xG, player/team xG summaries | JSONP extraction from HTML | ~1-2 req/sec |
| **StatsBomb Open Data** | Full event data (select competitions) | `statsbombpy` library | Unlimited (GitHub) |
| **ClubElo** | Historical team Elo ratings | CSV API | Generous |
| **football-data.co.uk** | Match results, basic stats | Static CSV download | None |

### 3.2 Pipeline Steps

```
GitHub Actions (Weekly Cron)

Step 1: IDENTITY LAYER
  Reep API → Download people.csv + teams.csv → Upsert into Turso

Step 2: STATS ACQUISITION
  FBref (soccerdata)    → Per-90 stats for top 5 leagues (6s between requests)
  Understat (JSONP)     → Shot-level xG + player/team xG (top 5 leagues + Russian PL)
  StatsBomb (statsbombpy)→ Full event data (open competitions only)
  ClubElo (CSV API)     → Current Elo ratings for all teams
  football-data.co.uk   → Match results + basic stats (static CSV)

Step 3: ENTITY RESOLUTION
  Match FBref player IDs → Reep IDs via key_fbref column in people.csv
  Match Understat IDs → Reep IDs via key_understat column
  All stats stored against reep_id as foreign key
  Fallback: fuzzy match on name + date_of_birth + nationality (confidence threshold)

Step 4: FEATURE COMPUTATION
  Per-90 normalisation (minimum 900 minutes)
  Percentile ranks by position + league
  xG/xA aggregation from Understat
  Player embeddings (stat vectors → cosine similarity)
  Team aggregate profiles
  Squad composition snapshots

Step 5: WRITE TO TURSO
  Upsert all computed data
```

### 3.3 Entity Resolution Flow

Reep is the identity layer. Every stat row links to a `reep_id`:

```
FBref player "dc7f8a28" (Cole Palmer)
  → Reep people.csv: key_fbref = "dc7f8a28" → reep_id = "reep_p2804f5db"

Understat player "1234"
  → Reep people.csv: key_understat = "1234" → reep_id = "reep_p2804f5db"

Same reep_id → unified profile with stats from both sources
```

### 3.4 Feature Computation Details

**Per-90 stats** (nutmeg methodology):
- Formula: `(stat / minutes_played) * 90`
- Only for players with 900+ minutes (10 full matches) — below this, per-90 is unreliable.
- Computed for: goals, assists, xG, xA, shots, key passes, progressive passes, progressive carries, tackles, interceptions, pressures.

**Percentile ranks:**
- Grouped by position AND league level (a Championship striker vs. other Championship strikers).
- Powers the radar charts on player profiles.

**Player embeddings:**
- Feature vector: ~20 per-90 stats + age + position encoding.
- Normalize all features to 0-1 range.
- Cosine similarity for "players like X".
- UMAP reduction for cluster visualization.

**Team profiles:**
- Aggregate squad per-90 stats (weighted by minutes).
- PPDA from Understat: `opponent_passes_in_own_half / defensive_actions_in_opponent_half`.
- Style classification: possession %, PPDA, directness (progressive passes ratio), set piece xG share.

### 3.5 Data Quality Checks

Each pipeline run validates:
- FBref: row counts per team/league (expect ~25 players per squad).
- Understat: xG values between 0-1, coordinates normalized 0-1.
- Entity resolution: log match rate (target >85% of top-5-league players matched to Reep IDs).
- Duplicate detection: same player appearing twice under different IDs.

### 3.6 Incremental Updates

- Weekly full refresh aligns with Reep's Monday update cycle.
- FBref stats only re-scraped for current season (historical seasons are stable).
- Understat: current season only for incremental, full history on first run.
- Pipeline logs stored in Turso for debugging.

### 3.7 Python Libraries

| Library | Purpose |
|---------|---------|
| `statsbombpy` | StatsBomb open data access |
| `soccerdata` | FBref + Understat scraping with built-in rate limiting and caching |
| `polars` | DataFrame processing (faster than pandas for large datasets) |
| `scikit-learn` | Player similarity embeddings, clustering |
| `libsql-client` | Turso database client |
| `kloppy` | Cross-provider coordinate normalization (for StatsBomb event data) |

### 3.8 Dev Tooling

[nutmeg](https://github.com/withqwerty/nutmeg) (Claude Code plugin) is used during development for:
- Writing correct FBref/Understat scraping code.
- Computing derived metrics (xG, PPDA, xT) with proper methodology.
- Handling provider-specific quirks (coordinate systems, qualifier IDs, rate limits).
- Data quality reviews via `/nutmeg-review`.

nutmeg is a dev-time accelerator, not shipped as part of the app.

## 4. Data Model (Turso Schema)

### 4.1 Identity Layer

```sql
CREATE TABLE people (
    reep_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,                 -- "player" or "coach"
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

CREATE INDEX idx_people_fbref ON people(key_fbref);
CREATE INDEX idx_people_understat ON people(key_understat);
CREATE INDEX idx_people_transfermarkt ON people(key_transfermarkt);
CREATE INDEX idx_people_name ON people(name);

CREATE TABLE teams (
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

CREATE INDEX idx_teams_fbref ON teams(key_fbref);
CREATE INDEX idx_teams_name ON teams(name);
```

### 4.2 Stats Layer

```sql
CREATE TABLE player_season_stats (
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

CREATE INDEX idx_pss_reep ON player_season_stats(reep_id);
CREATE INDEX idx_pss_team ON player_season_stats(team_reep_id);
CREATE INDEX idx_pss_season ON player_season_stats(season, league);

CREATE TABLE shots (
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

CREATE INDEX idx_shots_reep ON shots(reep_id);
CREATE INDEX idx_shots_season ON shots(season, league);

CREATE TABLE team_season_stats (
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

CREATE INDEX idx_tss_reep ON team_season_stats(reep_id);

CREATE TABLE squad_membership (
    reep_id TEXT NOT NULL REFERENCES people(reep_id),
    team_reep_id TEXT NOT NULL REFERENCES teams(reep_id),
    season TEXT NOT NULL,
    league TEXT NOT NULL,
    PRIMARY KEY (reep_id, team_reep_id, season)
);

CREATE INDEX idx_squad_team ON squad_membership(team_reep_id, season);
```

### 4.3 Computed Layer

```sql
CREATE TABLE player_per90 (
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

CREATE TABLE player_embeddings (
    reep_id TEXT PRIMARY KEY,
    season TEXT NOT NULL,
    embedding BLOB NOT NULL,
    cluster_id INTEGER,
    cluster_label TEXT,
    computed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE team_profiles (
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

CREATE TABLE pipeline_runs (
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

### 4.4 Key Design Decisions

- **`reep_id` is the foreign key everywhere** — no provider-specific IDs leak into stats/computed tables.
- **Source column on stats tables** — know where data came from, re-fetch selectively.
- **Embeddings stored as BLOB** — serialized float32 arrays, loaded with `numpy.frombuffer()`.
- **Percentiles precomputed** — avoids expensive queries at read time; recalculated weekly.
- **900-minute filter** baked into `player_per90` — only qualified players get per-90 rows.
- **`pipeline_runs` table** — tracks data freshness and match rates for debugging.

## 5. Feature Modules

### 5.1 Module 1: Player Intelligence

**Search and Discovery:**
- Search by name via Reep API `/search` endpoint.
- Results show name, nationality, position, age, and which providers have data.
- Clicking a player resolves their full cross-provider profile via Reep ID.

**Unified Player Profile:**
- Hero card: bio, current team, position, physical stats (from Reep people data). Player photos sourced from a provider with image URLs (e.g., Transfermarkt via link construction from ID, or a placeholder silhouette if unavailable).
- Stats tabs pulling from different providers via Reep ID mappings:
  - FBref: per-90 stats, season history, percentile ranks.
  - Understat: xG data, shot-level detail.
- All linked automatically — user never needs to know which provider the data comes from.

**Player Comparison:**
- Select 2-4 players, see side-by-side radar charts.
- Stat categories: shooting, passing, defending, progression, physical.
- Normalize per-90 and by position.

**Player Similarity Engine (ML):**
- Precomputed embeddings from career stat vectors (per-90 stats, position, age, league level).
- "Players like X" query returns top-N similar players ranked by cosine similarity.
- Clustering visualization: UMAP plot showing player archetypes (ball-playing CBs, creative 10s, pressing forwards, etc.).

### 5.2 Module 2: Team and Squad Analytics

**Squad Explorer:**
- Select a team → see full squad pulled from provider data.
- Breakdown views: by position, age distribution, nationality mix.
- Positional depth chart: who plays where, how many options per position.

**Squad Comparison:**
- Compare two squads side-by-side on aggregate stats.
- Radar at the team level: attacking output, defensive solidity, possession style.
- Age profile overlay: which squad is younger, which is in its prime window.

**Gap Analysis:**
- Highlight positions where a team is thin (e.g., only one natural LB).
- Flag age risk: positions where starters are 30+ with no young backup.

### 5.3 Module 3: Player-Team Fit (Signature Feature)

**"How would Player X fit in Team Y?"**
- Select a player + a target team.
- System compares the player's stat profile against the team's current players in that position.
- Outputs:
  - Percentile rank vs. current squad at that position.
  - Overlap/complement score: does this player fill a gap or duplicate what they have?
  - Style fit: does the player's profile match the team's playing style?
- Combines the similarity engine with squad composition data.

## 6. Frontend Pages

### 6.1 Home / Search

- Search bar with autocomplete via Reep `/search`.
- Toggle: Players | Teams.
- Recent/trending searches.
- Quick links to top leagues.

### 6.2 Player Profile (`/player/:reep_id`)

- Hero card: name, age, nationality, position, current team, height (photo if available via Transfermarkt ID, else placeholder).
- **Stats tab**: Per-90 stats table for current + past seasons, source badges.
- **Radar tab**: Percentile radar chart vs. position peers in same league.
- **xG tab**: Shot map, xG timeline across season, xG vs actual goals.
- **Similar players tab**: Top 10 similar players, UMAP cluster plot.
- **Fit analysis**: Dropdown to select a team → fit score, position rank, style compatibility.

### 6.3 Player Comparison (`/compare?p=reep_id1&p=reep_id2`)

- Side-by-side radar charts (up to 4 players).
- Stat-by-stat table with highlighting.
- Season trajectory overlay (xG over time, goals over time).

### 6.4 Team Profile (`/team/:reep_id`)

- Hero card: name, crest, country, stadium, founded, current Elo.
- **Squad tab**: Full squad table sortable by position/age/minutes, positional depth chart.
- **Stats tab**: Team season stats, xG for/against, PPDA.
- **Style tab**: Team style radar (possession, pressing, directness, set piece reliance).
- **Gap analysis tab**: Positions flagged thin or aging, suggested profile for ideal signing.

### 6.5 Squad Comparison (`/compare-teams?t=reep_id1&t=reep_id2`)

- Side-by-side team radars.
- Age distribution overlay.
- Position-by-position comparison.
- Elo trajectory chart.

### 6.6 Explore (`/explore`)

- Scatter plot builder: pick X and Y axis from any per-90 stat, colored by position/league.
- Cluster map: UMAP visualization of all player archetypes, clickable to drill into profiles.
- League selector to filter scope.

## 7. API Endpoints (FastAPI)

```
# Search and Identity
GET  /api/search?q={name}&type={player|team}
GET  /api/player/{reep_id}
GET  /api/team/{reep_id}

# Stats
GET  /api/player/{reep_id}/stats?season={season}
GET  /api/player/{reep_id}/shots?season={season}
GET  /api/team/{reep_id}/stats?season={season}
GET  /api/team/{reep_id}/squad?season={season}

# ML / Computed
GET  /api/player/{reep_id}/similar?n={10}
GET  /api/player/{reep_id}/fit?team={reep_id}
GET  /api/player/{reep_id}/radar?season={season}
GET  /api/team/{reep_id}/profile?season={season}
GET  /api/team/{reep_id}/gaps?season={season}

# Comparison
GET  /api/compare/players?ids={id1,id2,id3}
GET  /api/compare/teams?ids={id1,id2}

# Explore
GET  /api/explore/scatter?x={stat}&y={stat}&league={league}&position={pos}
GET  /api/explore/clusters?season={season}

# Meta
GET  /api/health
```

## 8. Tech Stack Summary

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14+ (App Router), Tailwind CSS, Recharts, D3 |
| Backend | FastAPI, Pydantic, libsql-client |
| ML | scikit-learn (cosine similarity, KMeans, UMAP), numpy |
| Pipeline | Python scripts, polars, soccerdata, statsbombpy |
| Database | Turso (libSQL) |
| Deployment | Vercel (frontend), Railway (backend), GitHub Actions (pipeline cron) |
| Dev tools | nutmeg (Claude Code plugin for football data guidance) |
