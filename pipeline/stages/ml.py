import sqlite3
from datetime import date

import numpy as np
import polars as pl
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

from pipeline.stages.compute import PER90_OUTPUT_NAMES

CLUSTER_LABELS = {
    0: "Goal Scorer",
    1: "Deep Defender",
    2: "Creative Playmaker",
    3: "Box-to-Box",
    4: "Pressing Forward",
    5: "Ball-Playing Defender",
    6: "Wide Attacker",
    7: "Defensive Midfielder",
}


def compute_embeddings(per90_df: pl.DataFrame) -> pl.DataFrame:
    stat_cols = [c for c in PER90_OUTPUT_NAMES if c in per90_df.columns]
    matrix = per90_df.select(stat_cols).fill_null(0).to_numpy().astype(np.float32)

    scaler = MinMaxScaler()
    normalized = scaler.fit_transform(matrix).astype(np.float32)

    reep_ids = per90_df["reep_id"].to_list()
    embeddings = [row.tobytes() for row in normalized]

    return pl.DataFrame(
        {
            "reep_id": reep_ids,
            "embedding": embeddings,
        }
    )


def find_similar_players(
    embeddings_df: pl.DataFrame,
    target_reep_id: str,
    n: int = 10,
) -> list[dict]:
    reep_ids = embeddings_df["reep_id"].to_list()
    raw_embeddings = embeddings_df["embedding"].to_list()

    vectors = np.array([np.frombuffer(e, dtype=np.float32) for e in raw_embeddings])

    if target_reep_id not in reep_ids:
        return []

    target_idx = reep_ids.index(target_reep_id)
    target_vec = vectors[target_idx].reshape(1, -1)

    similarities = cosine_similarity(target_vec, vectors)[0]

    indices = np.argsort(similarities)[::-1]
    results = []
    for idx in indices:
        if reep_ids[idx] == target_reep_id:
            continue
        results.append(
            {
                "reep_id": reep_ids[idx],
                "similarity": round(float(similarities[idx]), 4),
            }
        )
        if len(results) >= n:
            break

    return results


def compute_clusters(
    embeddings_df: pl.DataFrame,
    n_clusters: int = 8,
) -> pl.DataFrame:
    reep_ids = embeddings_df["reep_id"].to_list()
    raw_embeddings = embeddings_df["embedding"].to_list()

    vectors = np.array([np.frombuffer(e, dtype=np.float32) for e in raw_embeddings])

    actual_clusters = min(n_clusters, len(vectors))

    kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
    cluster_ids = kmeans.fit_predict(vectors)

    try:
        import umap

        reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=min(15, len(vectors) - 1))
        coords = reducer.fit_transform(vectors)
        umap_x = coords[:, 0].tolist()
        umap_y = coords[:, 1].tolist()
    except Exception:
        from sklearn.decomposition import PCA

        pca = PCA(n_components=2, random_state=42)
        coords = pca.fit_transform(vectors)
        umap_x = coords[:, 0].tolist()
        umap_y = coords[:, 1].tolist()

    labels = [CLUSTER_LABELS.get(int(c), f"Cluster {c}") for c in cluster_ids]

    return pl.DataFrame(
        {
            "reep_id": reep_ids,
            "cluster_id": [int(c) for c in cluster_ids],
            "cluster_label": labels,
            "umap_x": umap_x,
            "umap_y": umap_y,
        }
    )


def _calculate_age(dob: str) -> int | None:
    try:
        birth = date.fromisoformat(dob)
        today = date.today()
        age = today.year - birth.year
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        return age
    except (ValueError, TypeError):
        return None


def compute_team_profiles(
    conn: sqlite3.Connection,
    season: str,
) -> list[dict]:
    teams_with_squads = conn.execute(
        """SELECT DISTINCT sm.team_reep_id, sm.league
           FROM squad_membership sm
           WHERE sm.season = ?""",
        (season,),
    ).fetchall()

    profiles = []
    for row in teams_with_squads:
        team_id, league = row[0], row[1]

        members = conn.execute(
            """SELECT p.reep_id, p.position, p.date_of_birth, p.nationality,
                      s.minutes_played
               FROM squad_membership sm
               JOIN people p ON sm.reep_id = p.reep_id
               LEFT JOIN player_season_stats s
                   ON sm.reep_id = s.reep_id AND sm.season = s.season AND sm.league = s.league
               WHERE sm.team_reep_id = ? AND sm.season = ?""",
            (team_id, season),
        ).fetchall()

        if not members:
            continue

        squad_size = len(members)
        ages = []
        pos_counts = {"FW": 0, "MF": 0, "DF": 0, "GK": 0}
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

        for m in members:
            if m[2]:
                age = _calculate_age(m[2])
                if age:
                    ages.append(age)
            if m[1]:
                pg = position_map.get(m[1], "MF")
                mins = m[4] or 0
                if mins >= 900:
                    pos_counts[pg] += 1

        team_stats = conn.execute(
            """SELECT ppda, xg, xga
               FROM team_season_stats
               WHERE reep_id = ? AND season = ? AND league = ?
               LIMIT 1""",
            (team_id, season, league),
        ).fetchone()

        ppda = team_stats[0] if team_stats and team_stats[0] else 10.0
        pressing_score = max(0, min(100, (15 - ppda) / 10 * 100))

        squad_stats = conn.execute(
            """SELECT SUM(passes_completed), SUM(passes_attempted), SUM(progressive_passes)
               FROM player_season_stats
               WHERE reep_id IN (
                   SELECT reep_id FROM squad_membership WHERE team_reep_id = ? AND season = ?
               ) AND season = ?""",
            (team_id, season, season),
        ).fetchone()

        pass_pct = (squad_stats[0] / squad_stats[1] * 100) if squad_stats and squad_stats[1] else 80
        possession_score = max(0, min(100, (pass_pct - 70) / 20 * 100))

        prog_passes = squad_stats[2] if squad_stats and squad_stats[2] else 0
        directness_score = max(0, min(100, prog_passes / 10))

        profiles.append(
            {
                "reep_id": team_id,
                "season": season,
                "league": league,
                "possession_score": round(possession_score, 1),
                "pressing_score": round(pressing_score, 1),
                "directness_score": round(directness_score, 1),
                "set_piece_reliance": 0.0,
                "avg_age": round(sum(ages) / len(ages), 1) if ages else None,
                "squad_size": squad_size,
                "foreign_player_pct": 0.0,
                "fw_depth": pos_counts["FW"],
                "mf_depth": pos_counts["MF"],
                "df_depth": pos_counts["DF"],
                "gk_depth": pos_counts["GK"],
            }
        )

    return profiles
