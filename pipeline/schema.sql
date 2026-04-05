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
