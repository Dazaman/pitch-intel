import polars as pl

from pipeline.stages.compute import compute_per90, compute_percentiles


def test_compute_per90():
    """Should calculate per-90 stats for players with 900+ minutes."""
    df = pl.DataFrame(
        {
            "reep_id": ["p1", "p2", "p3"],
            "minutes_played": [2700, 900, 450],  # p3 below threshold
            "goals": [18, 6, 5],
            "assists": [9, 3, 4],
            "xg": [15.0, 5.5, 4.0],
            "xa": [8.0, 2.5, 3.0],
            "shots": [80, 30, 25],
            "key_passes": [50, 20, 18],
            "progressive_passes": [70, 25, 20],
            "progressive_carries": [55, 18, 15],
            "tackles": [20, 30, 10],
            "interceptions": [15, 22, 8],
            "pressures": [150, 200, 100],
            "take_ons_succeeded": [40, 15, 12],
        }
    )

    result = compute_per90(df)

    # p3 should be excluded (< 900 minutes)
    assert len(result) == 2

    p1 = result.filter(pl.col("reep_id") == "p1")
    # goals_per90 = (18 / 2700) * 90 = 0.6
    assert abs(p1["goals_per90"][0] - 0.6) < 0.01
    # xg_per90 = (15.0 / 2700) * 90 = 0.5
    assert abs(p1["xg_per90"][0] - 0.5) < 0.01


def test_compute_percentiles():
    """Should compute percentile ranks within a group."""
    df = pl.DataFrame(
        {
            "reep_id": ["p1", "p2", "p3", "p4", "p5"],
            "position_group": ["FW", "FW", "FW", "FW", "FW"],
            "goals_per90": [0.8, 0.6, 0.4, 0.2, 0.1],
            "xg_per90": [0.7, 0.5, 0.4, 0.3, 0.1],
            "assists_per90": [0.3, 0.4, 0.2, 0.1, 0.5],
            "xa_per90": [0.2, 0.3, 0.1, 0.15, 0.4],
            "shots_per90": [4.0, 3.0, 2.5, 2.0, 1.5],
            "key_passes_per90": [1.5, 1.2, 1.0, 0.8, 2.0],
            "progressive_passes_per90": [2.0, 1.8, 1.5, 1.2, 2.5],
            "progressive_carries_per90": [1.5, 1.2, 1.0, 0.8, 1.8],
            "tackles_per90": [0.5, 0.8, 1.0, 1.2, 0.3],
            "interceptions_per90": [0.3, 0.5, 0.7, 0.9, 0.2],
            "pressures_per90": [5.0, 6.0, 7.0, 8.0, 4.0],
            "take_ons_per90": [2.0, 1.5, 1.0, 0.5, 2.5],
        }
    )

    result = compute_percentiles(df)

    p1 = result.filter(pl.col("reep_id") == "p1")
    # p1 has highest goals_per90 (0.8) among 5 players -> top percentile
    assert p1["goals_pctile"][0] >= 80

    # p5 has lowest goals_per90 (0.1) -> low percentile
    p5 = result.filter(pl.col("reep_id") == "p5")
    assert p5["goals_pctile"][0] <= 20
