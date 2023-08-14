def expected_outcome(ratingA, ratingB):
    return 1 / (1 + 10 ** ((ratingB - ratingA) / 400))

def predict_winner(teamA_elo, teamB_elo):
    if expected_outcome(teamA_elo, teamB_elo) > 0.5:
        return "Team A"
    else:
        return "Team B"