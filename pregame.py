from sportsdata import SportsDataService
from scoring import score_confidence

def pregame_prediction(player_id, prop_line):
    sds = SportsDataService()
    # Fetch last 5 games
    stats = sds.get_player_game_stats(player_id)
    last5 = stats[-5:] if len(stats) >= 5 else stats
    # Average last 5 games
    avg_last5 = sum([g['FantasyPoints'] for g in last5]) / len(last5) if last5 else 0
    # Season stats
    season_stats = sds.get_fantasy_projections(player_id)
    season_avg = season_stats.get('FantasyPoints', avg_last5)
    # Fantasy projections (current week)
    projections = sds.get_fantasy_projections(player_id)
    proj = projections.get('FantasyPoints', season_avg)
    # Average all
    avg = (avg_last5 + season_avg + proj) / 3
    # Compare to prop line
    prediction = 'Over' if avg > prop_line else 'Under'
    confidence = score_confidence(avg, prop_line)
    return {
        'player_id': player_id,
        'avg_last5': avg_last5,
        'season_avg': season_avg,
        'projection': proj,
        'predicted': avg,
        'prop_line': prop_line,
        'prediction': prediction,
        'confidence': confidence
    }
