import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
REEP_API_KEY = os.environ.get("REEP_API_KEY", "")

REEP_BASE_URL = "https://github.com/withqwerty/reep/raw/main/data"

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

TOP_5_LEAGUES = {
    "ENG-Premier League": "Premier League",
    "ESP-La Liga": "La Liga",
    "ITA-Serie A": "Serie A",
    "GER-Bundesliga": "Bundesliga",
    "FRA-Ligue 1": "Ligue 1",
}

UNDERSTAT_LEAGUES = [
    "ENG-Premier League",
    "ESP-La Liga",
    "GER-Bundesliga",
    "ITA-Serie A",
    "FRA-Ligue 1",
]

CURRENT_SEASON = "2025-2026"

MIN_MINUTES_FOR_PER90 = 900

POSITION_GROUPS = {
    "goalkeeper": "GK",
    "centre-back": "DF",
    "left-back": "DF",
    "right-back": "DF",
    "defensive midfield": "MF",
    "central midfield": "MF",
    "attacking midfield": "MF",
    "left midfield": "MF",
    "right midfield": "MF",
    "left winger": "FW",
    "right winger": "FW",
    "centre-forward": "FW",
    "second striker": "FW",
}
