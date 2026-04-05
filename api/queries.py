SEARCH_PEOPLE = """
    SELECT reep_id, type, name, nationality, position, date_of_birth
    FROM people
    WHERE name LIKE ? COLLATE NOCASE
    ORDER BY name
    LIMIT 20
"""

SEARCH_TEAMS = """
    SELECT reep_id, name, country, stadium
    FROM teams
    WHERE name LIKE ? COLLATE NOCASE
    ORDER BY name
    LIMIT 20
"""

GET_PLAYER = """
    SELECT reep_id, type, name, full_name, date_of_birth, nationality,
           position, height_cm, key_transfermarkt, key_fbref
    FROM people
    WHERE reep_id = ?
"""

GET_PLAYER_STATS = """
    SELECT season, league, source, minutes_played, games, starts,
           goals, assists, xg, npxg, xa, shots, shots_on_target,
           key_passes, passes_completed, passes_attempted,
           progressive_passes, progressive_carries,
           tackles, interceptions, pressures,
           take_ons_attempted, take_ons_succeeded,
           yellow_cards, red_cards
    FROM player_season_stats
    WHERE reep_id = ?
    ORDER BY season DESC
"""

GET_PLAYER_STATS_BY_SEASON = """
    SELECT season, league, source, minutes_played, games, starts,
           goals, assists, xg, npxg, xa, shots, shots_on_target,
           key_passes, passes_completed, passes_attempted,
           progressive_passes, progressive_carries,
           tackles, interceptions, pressures,
           take_ons_attempted, take_ons_succeeded,
           yellow_cards, red_cards
    FROM player_season_stats
    WHERE reep_id = ? AND season = ?
    ORDER BY league
"""

GET_PLAYER_SHOTS = """
    SELECT id, minute, result, x, y, xg, situation, shot_type
    FROM shots
    WHERE reep_id = ?
    ORDER BY minute
"""

GET_PLAYER_SHOTS_BY_SEASON = """
    SELECT id, minute, result, x, y, xg, situation, shot_type
    FROM shots
    WHERE reep_id = ? AND season = ?
    ORDER BY minute
"""

GET_PLAYER_RADAR = """
    SELECT reep_id, season, league, position_group, minutes_played,
           goals_per90, xg_per90, assists_per90, xa_per90,
           shots_per90, key_passes_per90,
           progressive_passes_per90, progressive_carries_per90,
           tackles_per90, interceptions_per90, pressures_per90, take_ons_per90,
           goals_pctile, xg_pctile, assists_pctile, xa_pctile,
           shots_pctile, key_passes_pctile,
           progressive_passes_pctile, progressive_carries_pctile,
           tackles_pctile, interceptions_pctile, pressures_pctile, take_ons_pctile
    FROM player_per90
    WHERE reep_id = ?
    ORDER BY season DESC
    LIMIT 1
"""

GET_PLAYER_RADAR_BY_SEASON = """
    SELECT reep_id, season, league, position_group, minutes_played,
           goals_per90, xg_per90, assists_per90, xa_per90,
           shots_per90, key_passes_per90,
           progressive_passes_per90, progressive_carries_per90,
           tackles_per90, interceptions_per90, pressures_per90, take_ons_per90,
           goals_pctile, xg_pctile, assists_pctile, xa_pctile,
           shots_pctile, key_passes_pctile,
           progressive_passes_pctile, progressive_carries_pctile,
           tackles_pctile, interceptions_pctile, pressures_pctile, take_ons_pctile
    FROM player_per90
    WHERE reep_id = ? AND season = ?
    LIMIT 1
"""

GET_TEAM = """
    SELECT reep_id, name, country, founded, stadium,
           key_transfermarkt, key_fbref
    FROM teams
    WHERE reep_id = ?
"""

GET_TEAM_STATS = """
    SELECT season, league, source, wins, draws, losses,
           goals_for, goals_against, xg, xga, ppda,
           elo_start, elo_end
    FROM team_season_stats
    WHERE reep_id = ?
    ORDER BY season DESC
"""

GET_TEAM_STATS_BY_SEASON = """
    SELECT season, league, source, wins, draws, losses,
           goals_for, goals_against, xg, xga, ppda,
           elo_start, elo_end
    FROM team_season_stats
    WHERE reep_id = ? AND season = ?
"""

GET_TEAM_SQUAD = """
    SELECT p.reep_id, p.name, p.position, p.nationality, p.date_of_birth,
           s.minutes_played, s.goals, s.assists, s.xg
    FROM squad_membership sm
    JOIN people p ON sm.reep_id = p.reep_id
    LEFT JOIN player_season_stats s
        ON sm.reep_id = s.reep_id AND sm.season = s.season AND sm.league = s.league
    WHERE sm.team_reep_id = ? AND sm.season = ?
    ORDER BY p.position, p.name
"""

HEALTH_CHECK = """
    SELECT status, started_at, people_count, teams_count
    FROM pipeline_runs
    ORDER BY id DESC
    LIMIT 1
"""
