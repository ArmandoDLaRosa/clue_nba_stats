import datetime
from sqlalchemy import text


def get_latest_game_date(db):
    sql_query = text("SELECT MAX(GAME_DATE_EST) as latest_date FROM games")
    latest_date = db.session.execute(sql_query).fetchone()[0]

    return latest_date + datetime.timedelta(days=1)

def fetch_recent_game_ids(db, team_id, game_date, num_games=10):
    sql_query = f"""
    SELECT GAME_ID 
    FROM team_stats 
    WHERE TEAM_ID = {team_id} AND GAME_ID IN (
        SELECT GAME_ID 
        FROM games 
        WHERE GAME_DATE_EST < '{game_date}' 
        ORDER BY GAME_DATE_EST DESC
    )
    LIMIT {num_games}
    """
    return pd.read_sql_query(sql_query, db.engine)['GAME_ID'].tolist()

import pandas as pd

def fetch_team_recent_stats(db, game_date, team_id, num_games=10):
    recent_game_ids = fetch_recent_game_ids(db, team_id, game_date, num_games)
    sql_query = f"""
    SELECT * 
    FROM team_stats
    WHERE TEAM_ID = {team_id} AND GAME_ID IN {tuple(recent_game_ids)}
    """
    columns_to_exclude = ['GAME_ID', 'TEAM_ID']
    
    return pd.read_sql_query(sql_query, db.engine).drop(columns=columns_to_exclude).mean(numeric_only=True)

def fetch_players_recent_stats(db, game_date, team_id, num_games=10):
    recent_game_ids = fetch_recent_game_ids(db, team_id, game_date, num_games)
    sql_query = f"""
    SELECT * 
    FROM game_details
    WHERE PLAYER_ID IN (
        SELECT PLAYER_ID FROM player_team_associations WHERE TEAM_ID = {team_id}
    )
    AND GAME_ID IN {tuple(recent_game_ids)}
    """
    player_stats = pd.read_sql_query(sql_query, db.engine)
    return player_stats.groupby('PLAYER_ID').mean(numeric_only=True).mean(numeric_only=True)

def prepare_data(db, game_date, team1_id, team2_id):
    team1_stats = fetch_team_recent_stats(db, game_date, team1_id)
    team2_stats = fetch_team_recent_stats(db, game_date, team2_id)
    
    team1_players = fetch_players_recent_stats(db, game_date, team1_id)
    team2_players = fetch_players_recent_stats(db, game_date, team2_id)

    combined_features = pd.concat([team1_stats, team2_stats, team1_players, team2_players], axis=0)
    return combined_features