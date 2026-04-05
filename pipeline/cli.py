from datetime import datetime
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
def run(local_db, season):
    """Run the full pipeline: identity -> stats -> resolve -> compute."""
    conn = get_connection(local_db)
    init_schema(conn)

    run_id = log_pipeline_run(conn, status="running")
    errors = []

    # Stage 1: Identity
    click.echo("Stage 1: Downloading Reep identity data...")
    try:
        from pipeline.stages.identity import download_reep_csvs, ingest_people_csv, ingest_teams_csv

        with TemporaryDirectory() as tmp:
            people_path, teams_path = download_reep_csvs(Path(tmp))
            people_count = ingest_people_csv(conn, people_path)
            teams_count = ingest_teams_csv(conn, teams_path)
            click.echo(f"  Loaded {people_count} people, {teams_count} teams.")
    except Exception as e:
        errors.append(f"Identity stage failed: {e}")
        click.echo(f"  ERROR: {e}")
        people_count = 0
        teams_count = 0

    # Stage 2a: FBref
    click.echo("Stage 2a: Fetching FBref stats...")
    fbref_total = 0
    for league_code, league_name in TOP_5_LEAGUES.items():
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

    # Stage 2b: Understat
    click.echo("Stage 2b: Fetching Understat stats...")
    understat_total = 0
    for league in UNDERSTAT_LEAGUES:
        try:
            from pipeline.stages.resolve import resolve_understat_to_reep
            from pipeline.stages.understat import (
                fetch_understat_league,
                normalize_understat_players,
            )

            players_raw, _ = fetch_understat_league(league, season)
            if players_raw is not None:
                normalized = normalize_understat_players(players_raw, season=season, league=league)
                resolved, unresolved = resolve_understat_to_reep(conn, normalized)
                if len(resolved) > 0:
                    upsert_player_stats(
                        conn, resolved.drop("understat_id", "player_name", "team_name")
                    )
                click.echo(f"  {league}: {len(resolved)} resolved, {len(unresolved)} unresolved.")
                understat_total += len(resolved)
        except Exception as e:
            errors.append(f"Understat {league}: {e}")
            click.echo(f"  {league} ERROR: {e}")

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

    # Log completion
    stats_fetched = fbref_total + understat_total
    status = "completed" if not errors else "completed_with_errors"
    conn.execute(
        """UPDATE pipeline_runs
           SET completed_at = ?, status = ?, people_count = ?, teams_count = ?,
               stats_fetched = ?, error_log = ?
           WHERE id = ?""",
        (
            datetime.utcnow().isoformat(),
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
