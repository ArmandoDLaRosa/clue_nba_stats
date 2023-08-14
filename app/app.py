from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import pickle
import pandas as pd 
import numpy as np
from utils.elo import predict_winner 
from utils.gral import get_team_id_from_name
from utils.ml import prepare_data, get_latest_game_date

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://auth_user:Aauth123@localhost/nba_stats'
db = SQLAlchemy(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/teams', methods=['GET'])
def get_teams():
    teams_query = text("SELECT NICKNAME FROM teams")
    
    teams = db.session.execute(teams_query).fetchall()

    teams_list = [{"team_name": team[0]} for team in teams]

    return jsonify(teams_list)

@app.route('/best_player/<int:season>', methods=['GET'])
def get_best_players(season):
    '''
    Calculates the "productivity" of a player based on the sum of their points (PTS), rebounds (REB), and assists (AST).
    '''
    season_dates_sql = text("""
    SELECT MIN(GAME_DATE_EST), MAX(GAME_DATE_EST) FROM games WHERE SEASON = :season;
    """)
    start_date, end_date = db.session.execute(season_dates_sql, {'season': season}).fetchone()

    best_players_sql = text("""
    SELECT 
        YEAR(games.GAME_DATE_EST) as year,    
        WEEK(games.GAME_DATE_EST) as week_number,
        players.PLAYER_NAME, 
        SUM(game_details.PTS + game_details.REB + game_details.AST) as productivity
    FROM 
        game_details
    JOIN 
        games ON game_details.GAME_ID = games.GAME_ID
    JOIN 
        players ON game_details.PLAYER_ID = players.PLAYER_ID
    WHERE 
        games.GAME_DATE_EST BETWEEN :start_date AND :end_date
    GROUP BY 
        YEAR(games.GAME_DATE_EST), WEEK(games.GAME_DATE_EST), players.PLAYER_NAME
    ORDER BY 
          year ASC, week_number ASC, week_number, productivity DESC;
    """)

    results = db.session.execute(best_players_sql, {'start_date': start_date, 'end_date': end_date}).fetchall()

    weekly_best_players = []
    processed_weeks = set()
    for year, week, player, productivity in results:
        key = f"{year}-W{week}"
        if key not in processed_weeks:
            weekly_best_players.append({
                'year_week': key,
                'player': player,
                'productivity': productivity
            })
            processed_weeks.add(key)

    return jsonify(weekly_best_players)


@app.route('/predict_elo', methods=['POST'])
def predict_elo():
    team1_name = request.json.get('team1')
    team2_name = request.json.get('team2')
    
    query = text("SELECT elo_rating FROM teams WHERE TEAM_ID=:team")
    
    team1_elo =  db.session.execute(query, {'team': get_team_id_from_name(db, team1_name)}).fetchone()[0]
    team2_elo =  db.session.execute(query, {'team': get_team_id_from_name(db, team2_name)}).fetchone()[0]
    
    winner = predict_winner(team1_elo, team2_elo)
    return jsonify({'prediction': winner})



@app.route('/predict_ml', methods=['POST'])
def predict_ml():
    
    with open('../prediction/model_.pkl', 'rb') as file:
        model = pickle.load(file)
    
    with open('../prediction/scaler_.pkl', 'rb') as file:
        scaler = pickle.load(file)
        
    home_id = get_team_id_from_name(db, request.json.get('home_team'))
    away_id = get_team_id_from_name(db, request.json.get('away_team'))
    
    data = prepare_data(db, get_latest_game_date(db), home_id, away_id).values
    X_scaled = scaler.transform([data])
    prediction = model.predict(X_scaled)[0]
    
    result = {'prediction': 'Home Team Wins' if prediction == 1 else 'Away Team Wins'}
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)