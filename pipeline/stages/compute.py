import polars as pl

from pipeline.config import MIN_MINUTES_FOR_PER90

PER90_STATS = [
    "goals",
    "xg",
    "assists",
    "xa",
    "shots",
    "key_passes",
    "progressive_passes",
    "progressive_carries",
    "tackles",
    "interceptions",
    "pressures",
    "take_ons_succeeded",
]

PER90_OUTPUT_NAMES = [
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
]


def compute_per90(df: pl.DataFrame) -> pl.DataFrame:
    """Compute per-90 stats for players with enough minutes.

    Input df must have reep_id, minutes_played, and the raw stat columns.
    Returns a DataFrame with reep_id + per-90 columns.
    """
    qualified = df.filter(pl.col("minutes_played") >= MIN_MINUTES_FOR_PER90)

    per90_exprs = []
    for raw, out in zip(PER90_STATS, PER90_OUTPUT_NAMES):
        if raw in qualified.columns:
            per90_exprs.append(
                (
                    pl.col(raw).cast(pl.Float64) / pl.col("minutes_played").cast(pl.Float64) * 90
                ).alias(out)
            )
        else:
            per90_exprs.append(pl.lit(None).cast(pl.Float64).alias(out))

    return qualified.select(
        "reep_id",
        *per90_exprs,
    )


def compute_percentiles(df: pl.DataFrame) -> pl.DataFrame:
    """Compute percentile ranks for per-90 stats within position groups.

    Input df must have position_group and the per-90 columns.
    Returns the same DataFrame with added _pctile columns.
    """
    pctile_exprs = []

    for per90_name in PER90_OUTPUT_NAMES:
        pctile_name = per90_name.replace("_per90", "_pctile")
        pctile_exprs.append(
            pl.col(per90_name)
            .rank("ordinal")
            .over("position_group")
            .truediv(pl.col(per90_name).count().over("position_group"))
            .mul(100)
            .cast(pl.Int64)
            .alias(pctile_name)
        )

    return df.with_columns(pctile_exprs)
