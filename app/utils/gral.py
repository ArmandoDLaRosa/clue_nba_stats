from sqlalchemy import text

def get_team_id_from_name(db, name):
    sql_query = text(f"SELECT TEAM_ID FROM teams WHERE LOWER(NICKNAME) = :team_name LIMIT 1")
    return db.session.execute(sql_query, {'team_name': name.lower()}).fetchone()[0]
