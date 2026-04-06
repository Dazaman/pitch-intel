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
    risk: str


class ClusterPoint(BaseModel):
    reep_id: str
    name: str
    position: str | None = None
    cluster_id: int
    cluster_label: str
    umap_x: float
    umap_y: float
