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
    for reep_id in reep_ids[:4]:
        rows = conn.execute(GET_PLAYER_STATS, (reep_id,)).fetchall()
        player = conn.execute("SELECT name FROM people WHERE reep_id = ?", (reep_id,)).fetchone()
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
    for reep_id in reep_ids[:2]:
        rows = conn.execute(GET_TEAM_STATS, (reep_id,)).fetchall()
        team = conn.execute("SELECT name FROM teams WHERE reep_id = ?", (reep_id,)).fetchone()
        name = team["name"] if team else reep_id
        result[reep_id] = {
            "name": name,
            "seasons": [TeamSeasonStats(**dict(row)).model_dump() for row in rows],
        }
    return result
