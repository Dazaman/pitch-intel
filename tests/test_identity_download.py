from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline.stages.identity import download_reep_csvs

FIXTURES = Path(__file__).parent / "fixtures"


def test_download_reep_csvs(tmp_path):
    """download_reep_csvs should fetch people.csv and teams.csv to a local dir."""
    people_bytes = (FIXTURES / "people_sample.csv").read_bytes()
    teams_bytes = (FIXTURES / "teams_sample.csv").read_bytes()

    def fake_get(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        if "people.csv" in url:
            resp.content = people_bytes
        elif "teams.csv" in url:
            resp.content = teams_bytes
        return resp

    with patch("httpx.get", side_effect=fake_get):
        people_path, teams_path = download_reep_csvs(tmp_path)

    assert people_path.exists()
    assert teams_path.exists()
    assert "Cole Palmer" in people_path.read_text()
    assert "Arsenal" in teams_path.read_text()
