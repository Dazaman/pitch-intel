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
