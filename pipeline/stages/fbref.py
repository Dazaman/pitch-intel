import pandas as pd
import polars as pl

# Map FBref multi-index columns to our flat column names.
COLUMN_MAP = {
    ("player", "player"): "player_name",
    ("team", "team"): "team_name",
    ("Playing Time", "Min"): "minutes_played",
    ("Playing Time", "MP"): "games",
    ("Playing Time", "Starts"): "starts",
    ("Performance", "Gls"): "goals",
    ("Performance", "Ast"): "assists",
    ("Expected", "xG"): "xg",
    ("Expected", "npxG"): "npxg",
    ("Expected", "xAG"): "xa",
    ("Performance", "Sh"): "shots",
    ("Performance", "SoT"): "shots_on_target",
    ("Total", "Cmp"): "passes_completed",
    ("Total", "Att"): "passes_attempted",
    ("progressive_passes", "PrgP"): "progressive_passes",
    ("progressive_carries", "PrgC"): "progressive_carries",
    ("progressive_passes_received", "PrgR"): "progressive_passes_received",
    ("Tackles", "Tkl"): "tackles",
    ("Int", "Int"): "interceptions",
    ("Blocks", "Blocks"): "blocks",
    ("Pressures", "Press"): "pressures",
    ("Pressures", "Succ"): "pressure_successes",
    ("Touches", "Touches"): "touches",
    ("Carries", "Carries"): "carries",
    ("Take-Ons", "Att"): "take_ons_attempted",
    ("Take-Ons", "Succ"): "take_ons_succeeded",
    ("Performance", "CrdY"): "yellow_cards",
    ("Performance", "CrdR"): "red_cards",
    ("Aerial Duels", "Won"): "aerials_won",
    ("Aerial Duels", "Lost"): "aerials_lost",
    ("SCA", "SCA"): "key_passes",
}


def _find_column(pdf_columns, level0_sub: str, level1_exact: str) -> str | None:
    """Find a pandas MultiIndex column by matching substrings."""
    for col in pdf_columns:
        if isinstance(col, tuple) and len(col) >= 2:
            if level0_sub in str(col[0]) and col[1] == level1_exact:
                return col
        elif col == level1_exact:
            return col
    return None


def normalize_fbref_stats(
    raw_df: pd.DataFrame,
    season: str,
    league: str,
) -> pl.DataFrame:
    """Normalize a raw soccerdata FBref DataFrame into our schema."""
    mapped = {}

    for (l0_sub, l1_exact), our_name in COLUMN_MAP.items():
        col = _find_column(raw_df.columns, l0_sub, l1_exact)
        if col is not None:
            mapped[our_name] = raw_df[col].tolist()
        else:
            mapped[our_name] = [None] * len(raw_df)

    mapped["season"] = [season] * len(raw_df)
    mapped["league"] = [league] * len(raw_df)
    mapped["source"] = ["fbref"] * len(raw_df)

    # Extract FBref player ID from the DataFrame index if available.
    if hasattr(raw_df, "index") and raw_df.index.name == "player":
        mapped["fbref_id"] = [str(idx) for idx in raw_df.index.tolist()]
    else:
        mapped["fbref_id"] = [None] * len(raw_df)

    return pl.DataFrame(mapped)


def fetch_fbref_season(league_code: str, season: str) -> pd.DataFrame | None:
    """Fetch player season stats from FBref via soccerdata.

    Returns None if the scraper fails.
    """
    try:
        import soccerdata as sd

        fbref = sd.FBref(leagues=league_code, seasons=season)
        return fbref.read_player_season_stats(stat_type="standard")
    except Exception as e:
        print(f"FBref fetch failed for {league_code} {season}: {e}")
        return None
