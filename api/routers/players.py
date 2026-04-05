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

PCTILE_FIELDS = [
    "goals_pctile",
    "xg_pctile",
    "assists_pctile",
    "xa_pctile",
    "shots_pctile",
    "key_passes_pctile",
    "progressive_passes_pctile",
    "progressive_carries_pctile",
    "tackles_pctile",
    "interceptions_pctile",
    "pressures_pctile",
    "take_ons_pctile",
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
