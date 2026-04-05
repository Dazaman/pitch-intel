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

    people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    teams = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]

    return HealthResponse(
        status="no_pipeline_runs",
        people_count=people,
        teams_count=teams,
    )
