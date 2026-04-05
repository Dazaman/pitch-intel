from unittest.mock import MagicMock, patch

import polars as pl

from pipeline.stages.clubelo import fetch_clubelo_ratings, parse_clubelo_csv


def test_parse_clubelo_csv():
    csv_text = """Rank,Club,Country,Level,Elo,From,To
1,Arsenal,ENG,1,2050,2025-08-01,2025-08-08
2,Chelsea,ENG,1,1980,2025-08-01,2025-08-08
3,Barcelona,ESP,1,2010,2025-08-01,2025-08-08"""

    result = parse_clubelo_csv(csv_text)

    assert isinstance(result, pl.DataFrame)
    assert len(result) == 3
    assert result["club"][0] == "Arsenal"
    assert result["elo"][0] == 2050
    assert result["country"][0] == "ENG"


def test_fetch_clubelo_ratings():
    csv_text = """Rank,Club,Country,Level,Elo,From,To
1,Arsenal,ENG,1,2050,2025-08-01,2025-08-08"""

    resp = MagicMock()
    resp.status_code = 200
    resp.text = csv_text
    resp.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=resp):
        result = fetch_clubelo_ratings("2025-08-01")

    assert len(result) == 1
    assert result["club"][0] == "Arsenal"
