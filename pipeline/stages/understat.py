import pandas as pd
import polars as pl


def normalize_understat_players(
    raw_df: pd.DataFrame,
    season: str,
    league: str,
) -> pl.DataFrame:
    """Normalize raw soccerdata Understat player data into our schema.

    soccerdata returns a MultiIndex DataFrame with index: league, season, team, player
    and columns: player_id, matches, minutes, goals, xg, np_xg, assists, xa, shots, etc.
    """
    df = raw_df.reset_index()

    return pl.DataFrame(
        {
            "understat_id": [str(x) for x in df["player_id"].tolist()],
            "player_name": df["player"].tolist(),
            "team_name": df["team"].tolist(),
            "team_id": [str(x) for x in df["team_id"].tolist()],
            "season": [season] * len(df),
            "league": [league] * len(df),
            "minutes_played": df["minutes"].tolist(),
            "games": df["matches"].tolist(),
            "goals": df["goals"].tolist(),
            "xg": df["xg"].tolist(),
            "npxg": df["np_xg"].tolist(),
            "assists": df["assists"].tolist(),
            "xa": df["xa"].tolist(),
            "shots": df["shots"].tolist(),
            "key_passes": df["key_passes"].tolist(),
            "source": ["understat"] * len(df),
        }
    )


def normalize_understat_shots(
    raw_df: pd.DataFrame,
    season: str,
    league: str,
) -> pl.DataFrame:
    """Normalize raw Understat shot data into our schema."""
    return pl.DataFrame(
        {
            "id": raw_df["id"].tolist(),
            "understat_player_id": [str(x) for x in raw_df["player_id"].tolist()],
            "match_id": [str(x) for x in raw_df["match_id"].tolist()],
            "season": [season] * len(raw_df),
            "league": [league] * len(raw_df),
            "minute": raw_df["minute"].tolist(),
            "result": raw_df["result"].tolist(),
            "x": raw_df["X"].tolist(),
            "y": raw_df["Y"].tolist(),
            "xg": raw_df["xG"].tolist(),
            "situation": raw_df["situation"].tolist(),
            "shot_type": raw_df["shotType"].tolist(),
            "last_action": raw_df["lastAction"].tolist(),
            "source": ["understat"] * len(raw_df),
        }
    )


def fetch_understat_league(
    league: str, season: str
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Fetch player stats and shot data from Understat via soccerdata."""
    try:
        import soccerdata as sd

        understat = sd.Understat(leagues=league, seasons=season)
        players = understat.read_player_season_stats()
        return players, None
    except Exception as e:
        print(f"Understat fetch failed for {league} {season}: {e}")
        return None, None
