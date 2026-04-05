import pandas as pd
import polars as pl


def normalize_understat_players(
    raw_df: pd.DataFrame,
    season: str,
    league: str,
) -> pl.DataFrame:
    """Normalize raw Understat player data into our schema."""
    return pl.DataFrame(
        {
            "understat_id": [str(x) for x in raw_df["id"].tolist()],
            "player_name": raw_df["player_name"].tolist(),
            "team_name": raw_df["team"].tolist(),
            "season": [season] * len(raw_df),
            "league": [league] * len(raw_df),
            "minutes_played": raw_df["time"].tolist(),
            "games": raw_df["games"].tolist(),
            "goals": raw_df["goals"].tolist(),
            "xg": raw_df["xG"].tolist(),
            "npxg": raw_df["npxG"].tolist(),
            "assists": raw_df["assists"].tolist(),
            "xa": raw_df["xA"].tolist(),
            "shots": raw_df["shots"].tolist(),
            "key_passes": raw_df["key_passes"].tolist(),
            "source": ["understat"] * len(raw_df),
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
