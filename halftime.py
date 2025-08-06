from sportsdata import SportsDataService
from scoring import score_confidence

def halftime_prediction(game_id, player_id, halftime_prop_line):
    sds = SportsDataService()
    # Get live player stats for first half
    stats = sds.get_live_player_stats(game_id)
    player_stats = next((p for p in stats if p['PlayerID'] == player_id), None)
    if not player_stats:
        return {'error': 'Player not found in live stats'}
    first_half_points = player_stats.get('FantasyPointsHalf', 0)
    # Estimate full game projection (double first half or use trend)
    projected_full = first_half_points * 2
    # Predict second half production
    second_half_proj = projected_full - first_half_points
    # Compare to halftime prop line
    prediction = 'Over' if second_half_proj > halftime_prop_line else 'Under'
    confidence = score_confidence(second_half_proj, halftime_prop_line)
    return {
        'player_id': player_id,
        'game_id': game_id,
        'first_half_points': first_half_points,
        'projected_full': projected_full,
        'second_half_proj': second_half_proj,
        'halftime_prop_line': halftime_prop_line,
        'prediction': prediction,
        'confidence': confidence
    }
