import io
from datetime import date

import httpx
import polars as pl


def parse_clubelo_csv(csv_text: str) -> pl.DataFrame:
    """Parse ClubElo CSV response into a polars DataFrame."""
    df = pl.read_csv(io.StringIO(csv_text), infer_schema_length=10000, null_values=["None", ""])
    return df.rename(
        {
            "Rank": "rank",
            "Club": "club",
            "Country": "country",
            "Level": "level",
            "Elo": "elo",
            "From": "from_date",
            "To": "to_date",
        }
    )


def fetch_clubelo_ratings(date_str: str | None = None) -> pl.DataFrame:
    """Fetch Elo ratings for all clubs on a given date.

    date_str format: "YYYY-MM-DD". Defaults to today.
    """
    if date_str is None:
        date_str = date.today().isoformat()

    resp = httpx.get(f"http://api.clubelo.com/{date_str}", timeout=30)
    resp.raise_for_status()

    return parse_clubelo_csv(resp.text)
