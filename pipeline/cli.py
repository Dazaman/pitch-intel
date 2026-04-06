from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import click

from pipeline.config import CURRENT_SEASON, TOP_5_LEAGUES, UNDERSTAT_LEAGUES
from pipeline.db import get_connection, init_schema, log_pipeline_run, upsert_player_stats


@click.group()
def main():
    """Pitch Intel data pipeline."""
    pass


@main.command()
@click.option(
    "--local-db", type=str, default=None, help="Path to local SQLite file (for dev/testing)"
)
def init(local_db):
    """Initialize the database schema."""
    conn = get_connection(local_db)
    init_schema(conn)
    click.echo("Schema initialized.")
    conn.close()


@main.command()
@click.option("--local-db", type=str, default=None)
@click.option("--season", type=str, default=CURRENT_SEASON)
@click.option(
    "--partial",
    type=str,
    default=None,
    help="Run only one league. Use soccerdata league code e.g. 'ENG-Premier League'",
)
@click.option(
    "--skip-identity",
    is_flag=True,
    default=False,
    help="Skip downloading Reep CSVs (use existing identity data)",
)
@click.option(
    "--skip-fbref",
    is_flag=True,
    default=False,
    help="Skip FBref stats fetching",
)
@click.option(
    "--skip-understat",
    is_flag=True,
    default=False,
    help="Skip Understat stats fetching",
)
def run(local_db, season, partial, skip_identity, skip_fbref, skip_understat):
    """Run the pipeline: identity -> stats -> resolve -> compute.

    Use --partial to limit to one league:

        pitch-intel run --partial "ENG-Premier League"

    Valid league codes: ENG-Premier League, ESP-La Liga, ITA-Serie A,
    GER-Bundesliga, FRA-Ligue 1
    """
    conn = get_connection(local_db)
    init_schema(conn)

    run_id = log_pipeline_run(conn, status="running")
    errors = []

    # Determine which leagues to fetch
    if partial:
        if partial in TOP_5_LEAGUES:
            leagues_to_fetch = {partial: TOP_5_LEAGUES[partial]}
        else:
            click.echo(f"Unknown league code: {partial}")
            click.echo(f"Valid codes: {', '.join(TOP_5_LEAGUES.keys())}")
            return
        # Understat uses the same league codes as soccerdata
        understat_to_fetch = [partial] if partial in UNDERSTAT_LEAGUES else []
        click.echo(f"Partial mode: {TOP_5_LEAGUES[partial]} only\n")
    else:
        leagues_to_fetch = TOP_5_LEAGUES
        understat_to_fetch = UNDERSTAT_LEAGUES

    people_count = 0
    teams_count = 0

    # Stage 1: Identity
    if not skip_identity:
        click.echo("Stage 1: Downloading Reep identity data...")
        try:
            from pipeline.stages.identity import (
                download_reep_csvs,
                ingest_people_csv,
                ingest_teams_csv,
            )

            with TemporaryDirectory() as tmp:
                people_path, teams_path = download_reep_csvs(Path(tmp))
                people_count = ingest_people_csv(conn, people_path)
                teams_count = ingest_teams_csv(conn, teams_path)
                click.echo(f"  Loaded {people_count} people, {teams_count} teams.")
        except Exception as e:
            errors.append(f"Identity stage failed: {e}")
            click.echo(f"  ERROR: {e}")
    else:
        click.echo("Stage 1: Skipped (--skip-identity)")
        people_count = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        teams_count = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]

    # Stage 2a: FBref
    fbref_total = 0
    if not skip_fbref:
        click.echo("Stage 2a: Fetching FBref stats...")
        for league_code, league_name in leagues_to_fetch.items():
            try:
                from pipeline.stages.fbref import fetch_fbref_season, normalize_fbref_stats

                raw = fetch_fbref_season(league_code, season)
                if raw is not None:
                    normalized = normalize_fbref_stats(raw, season=season, league=league_name)
                    click.echo(f"  {league_name}: {len(normalized)} players fetched.")
                    fbref_total += len(normalized)
            except Exception as e:
                errors.append(f"FBref {league_name}: {e}")
                click.echo(f"  {league_name} ERROR: {e}")
    else:
        click.echo("Stage 2a: Skipped (--skip-fbref)")

    # Stage 2b: Understat
    understat_total = 0
    if not skip_understat:
        click.echo("Stage 2b: Fetching Understat stats...")
        for league in understat_to_fetch:
            try:
                from pipeline.stages.resolve import resolve_understat_to_reep
                from pipeline.stages.understat import (
                    fetch_understat_league,
                    normalize_understat_players,
                )

                players_raw, _ = fetch_understat_league(league, season)
                if players_raw is not None:
                    normalized = normalize_understat_players(
                        players_raw, season=season, league=league
                    )
                    resolved, unresolved = resolve_understat_to_reep(conn, normalized)
                    if len(resolved) > 0:
                        upsert_player_stats(
                            conn, resolved.drop("understat_id", "player_name", "team_name")
                        )
                    click.echo(
                        f"  {league}: {len(resolved)} resolved, {len(unresolved)} unresolved."
                    )
                    understat_total += len(resolved)
            except Exception as e:
                errors.append(f"Understat {league}: {e}")
                click.echo(f"  {league} ERROR: {e}")
    else:
        click.echo("Stage 2b: Skipped (--skip-understat)")

    # Stage 2c: ClubElo
    click.echo("Stage 2c: Fetching ClubElo ratings...")
    try:
        from pipeline.stages.clubelo import fetch_clubelo_ratings
        from pipeline.stages.resolve import resolve_clubelo_to_reep

        elo_df = fetch_clubelo_ratings()
        resolved_elo, _ = resolve_clubelo_to_reep(conn, elo_df)
        click.echo(f"  {len(resolved_elo)} teams with Elo ratings.")
    except Exception as e:
        errors.append(f"ClubElo: {e}")
        click.echo(f"  ERROR: {e}")

    # Stage 4: Compute
    click.echo("Stage 4: Computing per-90 stats and percentiles...")
    try:
        import polars as pl

        from pipeline.stages.compute import compute_per90

        rows = conn.execute(
            "SELECT * FROM player_season_stats WHERE season = ?", (season,)
        ).fetchall()
        if rows:
            columns = [
                desc[0]
                for desc in conn.execute("SELECT * FROM player_season_stats LIMIT 0").description
            ]
            stats_df = pl.DataFrame([dict(zip(columns, row)) for row in rows])
            per90 = compute_per90(stats_df)
            click.echo(f"  {len(per90)} players with per-90 stats.")
        else:
            click.echo("  No stats to compute per-90 for.")
    except Exception as e:
        errors.append(f"Compute: {e}")
        click.echo(f"  ERROR: {e}")

    # Stage 5: ML features
    click.echo("Stage 5: Computing ML features...")
    try:
        import polars as pl

        from pipeline.db import upsert_embeddings, upsert_team_profiles
        from pipeline.stages.ml import compute_clusters, compute_embeddings, compute_team_profiles

        per90_rows = conn.execute(
            "SELECT * FROM player_per90 WHERE season = ?", (season,)
        ).fetchall()
        if per90_rows:
            per90_cols = [
                desc[0] for desc in conn.execute("SELECT * FROM player_per90 LIMIT 0").description
            ]
            per90_df = pl.DataFrame([dict(zip(per90_cols, row)) for row in per90_rows])

            emb_df = compute_embeddings(per90_df)
            emb_df = emb_df.with_columns(pl.lit(season).alias("season"))

            clustered = compute_clusters(emb_df)
            emb_with_clusters = emb_df.join(
                clustered.select("reep_id", "cluster_id", "cluster_label"),
                on="reep_id",
            )
            upsert_embeddings(conn, emb_with_clusters)
            click.echo(f"  {len(emb_with_clusters)} player embeddings computed.")
        else:
            click.echo("  No per-90 data for embeddings.")

        profiles = compute_team_profiles(conn, season)
        if profiles:
            upsert_team_profiles(conn, profiles)
            click.echo(f"  {len(profiles)} team profiles computed.")
        else:
            click.echo("  No team profiles to compute (no squad data).")
    except Exception as e:
        errors.append(f"ML features: {e}")
        click.echo(f"  ERROR: {e}")

    # Log completion
    stats_fetched = fbref_total + understat_total
    status = "completed" if not errors else "completed_with_errors"
    conn.execute(
        """UPDATE pipeline_runs
           SET completed_at = ?, status = ?, people_count = ?, teams_count = ?,
               stats_fetched = ?, error_log = ?
           WHERE id = ?""",
        (
            datetime.now(UTC).isoformat(),
            status,
            people_count,
            teams_count,
            stats_fetched,
            "\n".join(errors) if errors else None,
            run_id,
        ),
    )
    conn.commit()

    click.echo(f"\nPipeline {status}. {len(errors)} errors.")
    if errors:
        for e in errors:
            click.echo(f"  - {e}")

    conn.close()


if __name__ == "__main__":
    main()
