from fastapi import APIRouter, HTTPException, Query

from api.deps import get_db
from api.models import ScatterPoint

router = APIRouter()

ALLOWED_STATS = {
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
}


@router.get("/explore/scatter", response_model=list[ScatterPoint])
def scatter(
    x: str = Query(description="Per-90 stat for X axis"),
    y: str = Query(description="Per-90 stat for Y axis"),
    league: str | None = Query(default=None),
    position: str | None = Query(default=None),
):
    if x not in ALLOWED_STATS or y not in ALLOWED_STATS:
        raise HTTPException(
            status_code=400,
            detail=f"Stats must be one of: {', '.join(sorted(ALLOWED_STATS))}",
        )

    conn = get_db()

    sql = f"""
        SELECT p90.reep_id, pe.name, pe.position, p90.league,
               p90.{x} as x_value, p90.{y} as y_value
        FROM player_per90 p90
        JOIN people pe ON p90.reep_id = pe.reep_id
        WHERE p90.{x} IS NOT NULL AND p90.{y} IS NOT NULL
    """
    params: list = []

    if league:
        sql += " AND p90.league = ?"
        params.append(league)

    if position:
        sql += " AND p90.position_group = ?"
        params.append(position)

    sql += " ORDER BY p90.reep_id LIMIT 500"

    rows = conn.execute(sql, params).fetchall()
    return [ScatterPoint(**dict(row)) for row in rows]


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
