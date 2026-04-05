import polars as pl

from pipeline.stages.understat import normalize_understat_players, normalize_understat_shots


def test_normalize_understat_players():
    """Should convert raw Understat player data to our schema."""
    import pandas as pd

    raw = pd.DataFrame(
        {
            "id": [10903, 7704],
            "player_name": ["Cole Palmer", "Cristiano Ronaldo"],
            "team": ["Chelsea", "Al Nassr"],
            "games": [32, 28],
            "time": [2800, 2400],
            "goals": [22, 15],
            "xG": [18.5, 14.2],
            "assists": [11, 4],
            "xA": [9.8, 3.5],
            "shots": [95, 88],
            "key_passes": [55, 30],
            "npg": [20, 13],
            "npxG": [16.2, 12.0],
        }
    )

    result = normalize_understat_players(raw, season="2024-2025", league="EPL")

    assert isinstance(result, pl.DataFrame)
    assert len(result) == 2
    assert result["understat_id"][0] == "10903"
    assert result["goals"][0] == 22
    assert result["xg"][0] == 18.5
    assert result["source"][0] == "understat"


def test_normalize_understat_shots():
    """Should convert raw Understat shot data to our schema."""
    import pandas as pd

    raw = pd.DataFrame(
        {
            "id": [501, 502],
            "player_id": [10903, 10903],
            "match_id": [100, 100],
            "minute": [23, 67],
            "result": ["Goal", "SavedShot"],
            "X": [0.89, 0.82],
            "Y": [0.45, 0.38],
            "xG": [0.76, 0.12],
            "situation": ["OpenPlay", "FromCorner"],
            "shotType": ["RightFoot", "Head"],
            "lastAction": ["Pass", "Cross"],
        }
    )

    result = normalize_understat_shots(raw, season="2024-2025", league="EPL")

    assert isinstance(result, pl.DataFrame)
    assert len(result) == 2
    assert result["id"][0] == 501
    assert result["xg"][0] == 0.76
    assert result["x"][0] == 0.89
    assert result["situation"][0] == "OpenPlay"
    assert result["shot_type"][0] == "RightFoot"
