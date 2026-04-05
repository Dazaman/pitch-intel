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
