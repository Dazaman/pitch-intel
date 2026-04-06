"""Seed a local SQLite database with sample football data for testing."""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.db import init_schema

DB_PATH = Path(__file__).parent.parent / "local.db"


def seed(conn: sqlite3.Connection) -> None:
    init_schema(conn)

    # --- People ---
    players = [
        ("reep_p2804f5db", "player", "Cole Palmer", "Cole Jermaine Palmer", "2002-05-06", "England", "attacking midfielder", 185, "568177", "dc7f8a28", "10903"),
        ("reep_p00000002", "player", "Bukayo Saka", "Bukayo Ayoyinka Saka", "2001-09-05", "England", "right winger", 178, "433177", "abc12345", "8260"),
        ("reep_p00000003", "player", "Erling Haaland", "Erling Braut Haaland", "2000-07-21", "Norway", "centre-forward", 194, "418560", "def67890", "9089"),
        ("reep_p00000004", "player", "Jude Bellingham", "Jude Victor William Bellingham", "2003-06-29", "England", "central midfield", 186, "581678", "ghi11111", "9910"),
        ("reep_p00000005", "player", "Vinicius Junior", "Vinicius Jose de Oliveira Junior", "2000-07-12", "Brazil", "left winger", 176, "339623", "jkl22222", "7140"),
        ("reep_p00000006", "player", "Rodri", "Rodrigo Hernandez Cascante", "1996-06-22", "Spain", "defensive midfield", 191, "357093", "mno33333", "5679"),
        ("reep_p00000007", "player", "William Saliba", "William Saliba", "2001-03-24", "France", "centre-back", 192, "516005", "pqr44444", "8899"),
        ("reep_p00000008", "player", "Mohamed Salah", "Mohamed Salah Hamed Mahrous Ghaly", "1992-06-15", "Egypt", "right winger", 175, "148455", "stu55555", "1245"),
        ("reep_p00000009", "player", "Phil Foden", "Philip Walter Foden", "2000-05-28", "England", "attacking midfielder", 171, "406635", "vwx66666", "7015"),
        ("reep_p00000010", "player", "Declan Rice", "Declan Rice", "1999-01-14", "England", "defensive midfield", 188, "357662", "yza77777", "7908"),
    ]

    conn.executemany(
        """INSERT OR REPLACE INTO people
           (reep_id, type, name, full_name, date_of_birth, nationality, position, height_cm,
            key_transfermarkt, key_fbref, key_understat)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        players,
    )

    # --- Teams ---
    teams = [
        ("reep_t0871097b", "Arsenal F.C.", "England", "1886-10-01", "Emirates Stadium", "11", "18bb7c10", "Arsenal"),
        ("reep_t00000002", "Chelsea F.C.", "England", "1905-03-10", "Stamford Bridge", "631", "cff3d9bb", "Chelsea"),
        ("reep_t00000003", "Manchester City", "England", "1880-04-16", "Etihad Stadium", "281", "b8fd03ef", "ManCity"),
        ("reep_t00000004", "Liverpool F.C.", "England", "1892-06-03", "Anfield", "31", "822bd0ba", "Liverpool"),
        ("reep_t00000005", "Real Madrid", "Spain", "1902-03-06", "Santiago Bernabeu", "418", "53a2f082", "RealMadrid"),
    ]

    conn.executemany(
        """INSERT OR REPLACE INTO teams
           (reep_id, name, country, founded, stadium, key_transfermarkt, key_fbref, key_clubelo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        teams,
    )

    # --- Player Season Stats (2024-2025, Premier League) ---
    stats = [
        # (reep_id, team_reep_id, season, league, source, min, games, starts, goals, assists, xg, npxg, xa, shots, sot, kp, pc, pa, pp, pcar, tackles, int, blocks, press, psucc, touches, carries, toa, tos, yc, rc, aw, al)
        ("reep_p2804f5db", "reep_t00000002", "2024-2025", "Premier League", "fbref", 2850, 33, 32, 22, 11, 18.5, 16.2, 9.8, 98, 44, 62, 1250, 1520, 88, 68, 22, 16, 11, 185, 58, 2300, 1450, 95, 52, 4, 0, 14, 9),
        ("reep_p00000002", "reep_t0871097b", "2024-2025", "Premier League", "fbref", 2650, 32, 30, 16, 12, 13.2, 11.8, 10.5, 78, 32, 58, 1100, 1380, 82, 75, 28, 20, 14, 210, 68, 2100, 1350, 88, 48, 5, 0, 18, 11),
        ("reep_p00000003", "reep_t00000003", "2024-2025", "Premier League", "fbref", 2400, 30, 28, 27, 5, 24.1, 21.8, 4.2, 115, 52, 22, 450, 620, 18, 25, 8, 5, 6, 120, 35, 1200, 580, 42, 22, 2, 0, 52, 28),
        ("reep_p00000004", "reep_t00000005", "2024-2025", "La Liga", "fbref", 2700, 32, 31, 19, 13, 15.8, 14.2, 11.2, 88, 38, 55, 1180, 1450, 78, 72, 32, 18, 12, 195, 62, 2250, 1380, 82, 45, 6, 0, 22, 15),
        ("reep_p00000005", "reep_t00000005", "2024-2025", "La Liga", "fbref", 2500, 30, 29, 15, 10, 12.5, 11.1, 8.8, 82, 30, 42, 980, 1250, 65, 95, 18, 12, 8, 165, 48, 2050, 1500, 110, 62, 7, 1, 12, 10),
        ("reep_p00000006", "reep_t00000003", "2024-2025", "Premier League", "fbref", 2900, 34, 34, 3, 8, 3.5, 2.8, 6.2, 28, 12, 45, 2200, 2450, 120, 55, 65, 42, 28, 280, 95, 3100, 1800, 35, 20, 8, 0, 25, 18),
        ("reep_p00000007", "reep_t0871097b", "2024-2025", "Premier League", "fbref", 3050, 35, 35, 2, 1, 1.8, 1.5, 0.8, 15, 5, 12, 1800, 1950, 95, 42, 52, 38, 32, 155, 52, 2400, 1100, 12, 5, 3, 0, 65, 22),
        ("reep_p00000008", "reep_t00000004", "2024-2025", "Premier League", "fbref", 2750, 33, 32, 18, 14, 15.2, 13.5, 12.1, 92, 40, 65, 1050, 1320, 72, 62, 20, 15, 10, 175, 55, 2150, 1280, 78, 42, 3, 0, 15, 12),
        ("reep_p00000009", "reep_t00000003", "2024-2025", "Premier League", "fbref", 2200, 28, 25, 14, 9, 11.8, 10.2, 7.5, 72, 30, 48, 1150, 1400, 75, 65, 18, 12, 8, 155, 48, 2000, 1250, 72, 38, 2, 0, 10, 8),
        ("reep_p00000010", "reep_t0871097b", "2024-2025", "Premier League", "fbref", 2800, 33, 33, 5, 7, 4.2, 3.5, 5.8, 35, 15, 38, 1900, 2150, 105, 48, 58, 35, 25, 265, 88, 2800, 1600, 28, 15, 6, 0, 32, 20),
    ]

    conn.executemany(
        """INSERT OR REPLACE INTO player_season_stats
           (reep_id, team_reep_id, season, league, source, minutes_played, games, starts,
            goals, assists, xg, npxg, xa, shots, shots_on_target, key_passes,
            passes_completed, passes_attempted, progressive_passes, progressive_carries,
            tackles, interceptions, blocks, pressures, pressure_successes,
            touches, carries, take_ons_attempted, take_ons_succeeded,
            yellow_cards, red_cards, aerials_won, aerials_lost)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        stats,
    )

    # --- Shots (sample for Cole Palmer) ---
    shots = [
        (1001, "reep_p2804f5db", "m001", "2024-2025", "Premier League", 12, "Goal", 0.88, 0.42, 0.72, "OpenPlay", "RightFoot", "Pass"),
        (1002, "reep_p2804f5db", "m001", "2024-2025", "Premier League", 34, "SavedShot", 0.82, 0.55, 0.08, "OpenPlay", "LeftFoot", "Dribble"),
        (1003, "reep_p2804f5db", "m002", "2024-2025", "Premier League", 67, "Goal", 0.91, 0.48, 0.85, "DirectFreekick", "RightFoot", "None"),
        (1004, "reep_p2804f5db", "m003", "2024-2025", "Premier League", 23, "MissedShots", 0.78, 0.38, 0.15, "OpenPlay", "RightFoot", "Cross"),
        (1005, "reep_p2804f5db", "m003", "2024-2025", "Premier League", 55, "Goal", 0.85, 0.50, 0.45, "OpenPlay", "RightFoot", "ThroughBall"),
        (1006, "reep_p2804f5db", "m004", "2024-2025", "Premier League", 8, "BlockedShot", 0.75, 0.60, 0.06, "FromCorner", "Head", "Cross"),
        (1007, "reep_p2804f5db", "m005", "2024-2025", "Premier League", 78, "Goal", 0.92, 0.45, 0.92, "Penalty", "RightFoot", "None"),
        (1008, "reep_p2804f5db", "m006", "2024-2025", "Premier League", 41, "SavedShot", 0.80, 0.52, 0.22, "OpenPlay", "LeftFoot", "Pass"),
        (1009, "reep_p2804f5db", "m007", "2024-2025", "Premier League", 63, "Goal", 0.87, 0.44, 0.55, "OpenPlay", "RightFoot", "Dribble"),
        (1010, "reep_p2804f5db", "m008", "2024-2025", "Premier League", 90, "Goal", 0.90, 0.47, 0.38, "SetPiece", "RightFoot", "Cross"),
    ]

    conn.executemany(
        """INSERT OR REPLACE INTO shots
           (id, reep_id, match_id, season, league, minute, result, x, y, xg, situation, shot_type, last_action)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        shots,
    )

    # --- Squad Membership ---
    squads = [
        # Arsenal
        ("reep_p00000002", "reep_t0871097b", "2024-2025", "Premier League"),
        ("reep_p00000007", "reep_t0871097b", "2024-2025", "Premier League"),
        ("reep_p00000010", "reep_t0871097b", "2024-2025", "Premier League"),
        # Chelsea
        ("reep_p2804f5db", "reep_t00000002", "2024-2025", "Premier League"),
        # Man City
        ("reep_p00000003", "reep_t00000003", "2024-2025", "Premier League"),
        ("reep_p00000006", "reep_t00000003", "2024-2025", "Premier League"),
        ("reep_p00000009", "reep_t00000003", "2024-2025", "Premier League"),
        # Liverpool
        ("reep_p00000008", "reep_t00000004", "2024-2025", "Premier League"),
        # Real Madrid
        ("reep_p00000004", "reep_t00000005", "2024-2025", "La Liga"),
        ("reep_p00000005", "reep_t00000005", "2024-2025", "La Liga"),
    ]

    conn.executemany(
        """INSERT OR REPLACE INTO squad_membership (reep_id, team_reep_id, season, league)
           VALUES (?, ?, ?, ?)""",
        squads,
    )

    # --- Player Per-90 + Percentiles (computed from stats above) ---
    per90_data = []
    position_map = {
        "reep_p2804f5db": ("MF", 2850),
        "reep_p00000002": ("FW", 2650),
        "reep_p00000003": ("FW", 2400),
        "reep_p00000006": ("MF", 2900),
        "reep_p00000007": ("DF", 3050),
        "reep_p00000008": ("FW", 2750),
        "reep_p00000009": ("MF", 2200),
        "reep_p00000010": ("MF", 2800),
    }

    raw_stats_by_id = {s[0]: s for s in stats if s[3] == "Premier League"}

    for reep_id, (pos_group, mins) in position_map.items():
        s = raw_stats_by_id.get(reep_id)
        if not s:
            continue

        def p90(val, minutes):
            return round((val / minutes) * 90, 2) if val and minutes else 0.0

        _, _, _, _, _, minutes, _, _, goals, assists, xg, _, xa, shots_val, _, kp, _, _, pp, pcar, tkl, inter, _, press, _, _, _, toa, tos, _, _, _, _ = s

        per90_row = (
            reep_id, "2024-2025", "Premier League", pos_group, minutes,
            p90(goals, minutes), p90(xg, minutes), p90(assists, minutes), p90(xa, minutes),
            p90(shots_val, minutes), p90(kp, minutes), p90(pp, minutes), p90(pcar, minutes),
            p90(tkl, minutes), p90(inter, minutes), p90(press, minutes), p90(tos, minutes),
            # Percentiles (simulated — ranked within this small sample)
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        )
        per90_data.append(per90_row)

    # Compute actual percentiles within position groups
    from collections import defaultdict

    groups = defaultdict(list)
    for row in per90_data:
        groups[row[3]].append(row)

    final_per90 = []
    for pos_group, rows in groups.items():
        stat_indices = list(range(5, 17))  # per90 stat columns
        pctile_indices = list(range(17, 29))  # percentile columns

        for stat_idx, pctile_idx in zip(stat_indices, pctile_indices):
            sorted_rows = sorted(rows, key=lambda r: r[stat_idx])
            for rank, row in enumerate(sorted_rows):
                pctile = int((rank + 1) / len(sorted_rows) * 100)
                row_list = list(row)
                row_list[pctile_idx] = pctile
                rows[rows.index(row)] = tuple(row_list)

        final_per90.extend(rows)

    conn.executemany(
        """INSERT OR REPLACE INTO player_per90
           (reep_id, season, league, position_group, minutes_played,
            goals_per90, xg_per90, assists_per90, xa_per90,
            shots_per90, key_passes_per90, progressive_passes_per90, progressive_carries_per90,
            tackles_per90, interceptions_per90, pressures_per90, take_ons_per90,
            goals_pctile, xg_pctile, assists_pctile, xa_pctile,
            shots_pctile, key_passes_pctile, progressive_passes_pctile, progressive_carries_pctile,
            tackles_pctile, interceptions_pctile, pressures_pctile, take_ons_pctile)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        final_per90,
    )

    # --- Team Season Stats ---
    team_stats = [
        ("reep_t0871097b", "2024-2025", "Premier League", "understat", 25, 8, 5, 80, 35, 78.5, 33.2, 8.5, 2020.0, 2050.0, 2055.0),
        ("reep_t00000002", "2024-2025", "Premier League", "understat", 18, 10, 10, 65, 52, 62.1, 48.8, 10.2, 1880.0, 1920.0, 1935.0),
        ("reep_t00000003", "2024-2025", "Premier League", "understat", 26, 6, 6, 85, 38, 82.3, 35.5, 7.8, 2040.0, 2080.0, 2095.0),
        ("reep_t00000004", "2024-2025", "Premier League", "understat", 24, 7, 7, 78, 40, 75.2, 38.1, 8.9, 2010.0, 2045.0, 2060.0),
        ("reep_t00000005", "2024-2025", "La Liga", "understat", 28, 4, 6, 88, 30, 85.1, 28.5, 9.1, 2060.0, 2100.0, 2110.0),
    ]

    conn.executemany(
        """INSERT OR REPLACE INTO team_season_stats
           (reep_id, season, league, source, wins, draws, losses, goals_for, goals_against,
            xg, xga, ppda, elo_start, elo_end, elo_peak)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        team_stats,
    )

    # --- Pipeline Run Log ---
    conn.execute(
        """INSERT INTO pipeline_runs (started_at, completed_at, status, people_count, teams_count, stats_fetched, match_rate)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("2026-04-06T10:00:00", "2026-04-06T10:05:00", "completed", 10, 5, 10, 100.0),
    )

    conn.commit()
    print(f"Seeded {DB_PATH}:")
    print(f"  {len(players)} players")
    print(f"  {len(teams)} teams")
    print(f"  {len(stats)} player season stats")
    print(f"  {len(shots)} shots")
    print(f"  {len(squads)} squad memberships")
    print(f"  {len(final_per90)} per-90 records")
    print(f"  {len(team_stats)} team season stats")


if __name__ == "__main__":
    conn = sqlite3.connect(str(DB_PATH))
    seed(conn)
    conn.close()
