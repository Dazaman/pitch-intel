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


@router.get("/player/{reep_id}/similar")
def get_similar_players(reep_id: str, n: int = Query(default=10, le=50)):
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity as cos_sim

    conn = get_db()

    target = conn.execute(
        "SELECT embedding FROM player_embeddings WHERE reep_id = ?", (reep_id,)
    ).fetchone()
    if not target:
        return []

    target_vec = np.frombuffer(target["embedding"], dtype=np.float32).reshape(1, -1)

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
        results.append(
            {
                "reep_id": rid,
                "name": names[rid],
                "position": positions[rid],
                "similarity": round(float(similarities[idx]), 4),
            }
        )
        if len(results) >= n:
            break

    return results


@router.get("/player/{reep_id}/fit")
def get_player_fit(reep_id: str, team: str = Query()):
    conn = get_db()

    player = conn.execute(
        "SELECT name, position FROM people WHERE reep_id = ?", (reep_id,)
    ).fetchone()
    team_row = conn.execute("SELECT name FROM teams WHERE reep_id = ?", (team,)).fetchone()

    if not player or not team_row:
        raise HTTPException(status_code=404, detail="Player or team not found")

    position_map = {
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
    pos_group = position_map.get(player["position"], "MF") if player["position"] else "MF"

    squad_per90 = conn.execute(
        """SELECT p90.reep_id, p90.xg_per90
           FROM player_per90 p90
           JOIN squad_membership sm ON p90.reep_id = sm.reep_id
           WHERE sm.team_reep_id = ? AND p90.position_group = ?
           ORDER BY p90.minutes_played DESC""",
        (team, pos_group),
    ).fetchall()

    player_per90 = conn.execute(
        "SELECT xg_per90 FROM player_per90 WHERE reep_id = ? ORDER BY season DESC LIMIT 1",
        (reep_id,),
    ).fetchone()

    position_rank = None
    position_total = len(squad_per90)
    if player_per90 and squad_per90:
        player_xg = player_per90["xg_per90"] or 0
        rank = sum(1 for s in squad_per90 if (s["xg_per90"] or 0) > player_xg) + 1
        position_rank = rank

    notes = []
    team_profile = conn.execute(
        "SELECT * FROM team_profiles WHERE reep_id = ? ORDER BY season DESC LIMIT 1",
        (team,),
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
