import polars as pl

from pipeline.stages.fbref import normalize_fbref_stats


def test_normalize_fbref_stats():
    """normalize_fbref_stats should produce a polars DataFrame with our schema columns."""
    import pandas as pd

    data = {
        ("Unnamed: player", "player"): ["Cole Palmer", "Bukayo Saka"],
        ("Unnamed: team", "team"): ["Chelsea", "Arsenal"],
        ("Playing Time", "Min"): [2800, 2500],
        ("Playing Time", "MP"): [32, 30],
        ("Playing Time", "Starts"): [30, 28],
        ("Performance", "Gls"): [22, 16],
        ("Performance", "Ast"): [11, 9],
        ("Expected", "xG"): [18.5, 12.3],
        ("Expected", "npxG"): [16.2, 11.1],
        ("Expected", "xAG"): [9.8, 8.5],
        ("Performance", "Sh"): [95, 72],
        ("Performance", "SoT"): [42, 30],
        ("Total", "Cmp"): [1200, 1100],
        ("Total", "Att"): [1500, 1400],
        ("Unnamed: progressive_passes", "PrgP"): [85, 78],
        ("Unnamed: progressive_carries", "PrgC"): [65, 70],
        ("Unnamed: progressive_passes_received", "PrgR"): [110, 95],
        ("Tackles", "Tkl"): [25, 35],
        ("Int", "Int"): [18, 22],
        ("Blocks", "Blocks"): [12, 15],
        ("Pressures", "Press"): [180, 220],
        ("Pressures", "Succ"): [55, 70],
        ("Touches", "Touches"): [2200, 2000],
        ("Carries", "Carries"): [1400, 1300],
        ("Take-Ons", "Att"): [90, 85],
        ("Take-Ons", "Succ"): [50, 45],
        ("Performance", "CrdY"): [3, 5],
        ("Performance", "CrdR"): [0, 0],
        ("Aerial Duels", "Won"): [15, 20],
        ("Aerial Duels", "Lost"): [10, 12],
    }

    pdf = pd.DataFrame(data)

    result = normalize_fbref_stats(pdf, season="2024-2025", league="Premier League")

    assert isinstance(result, pl.DataFrame)
    assert len(result) == 2
    assert "player_name" in result.columns
    assert "goals" in result.columns
    assert "xg" in result.columns
    assert result.filter(pl.col("player_name") == "Cole Palmer")["goals"][0] == 22
    assert result["season"][0] == "2024-2025"
    assert result["league"][0] == "Premier League"
    assert result["source"][0] == "fbref"


def test_normalize_fbref_stats_handles_missing_columns():
    """Should not crash when optional columns are missing."""
    import pandas as pd

    data = {
        ("Unnamed: player", "player"): ["Test Player"],
        ("Unnamed: team", "team"): ["Test FC"],
        ("Playing Time", "Min"): [900],
        ("Playing Time", "MP"): [10],
        ("Playing Time", "Starts"): [10],
        ("Performance", "Gls"): [5],
    }

    pdf = pd.DataFrame(data)

    result = normalize_fbref_stats(pdf, season="2024-2025", league="Premier League")

    assert len(result) == 1
    assert result["goals"][0] == 5
    assert result["xg"][0] is None
