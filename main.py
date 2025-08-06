from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv

from pregame import pregame_prediction
from halftime import halftime_prediction
from sportsdata import SportsDataService

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Stats Sync API",
    description="Sports prediction API with SportsDataIO integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def frontend():
    """Serve the frontend dashboard"""
    with open("frontend.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "stats-sync-api"}

@app.get("/pregame/{player_id}")
def pregame_route(player_id: int, prop_line: float = Query(..., description="Current prop line for the player")):
    """Pregame prediction for a player"""
    try:
        result = pregame_prediction(player_id, prop_line)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/halftime/{game_id}")
def halftime_route(game_id: int, player_id: int = Query(..., description="Player ID for halftime prediction"), halftime_prop_line: float = Query(..., description="Halftime prop line")):
    """Halftime prediction for a player in a game"""
    try:
        result = halftime_prediction(game_id, player_id, halftime_prop_line)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/liveprops/{game_id}")
def liveprops_route(game_id: int):
    """Get live player stats for a game"""
    try:
        sds = SportsDataService()
        stats = sds.get_live_player_stats(game_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedule")
def schedule_route(season: str = "2025REG"):
    """Get NFL schedule"""
    try:
        sds = SportsDataService()
        schedule = sds.get_nfl_schedule(season)
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player-stats/{player_id}")
def player_stats_route(player_id: int, season: str = "2025REG"):
    """Get player game stats"""
    try:
        sds = SportsDataService()
        stats = sds.get_player_game_stats(player_id, season)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/props/types")
def get_prop_types_route():
    """Get available prop types that map to FanDuel"""
    try:
        sds = SportsDataService()
        prop_types = sds.get_available_prop_types()
        return {"prop_types": prop_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/props/{game_id}")
def props_route(game_id: int):
    """Get player props for a game"""
    try:
        sds = SportsDataService()
        props = sds.get_player_props_by_game(game_id)
        return props
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/players/search")
def search_players_route(name: str):
    """Search for players by name"""
    try:
        sds = SportsDataService()
        players = sds.search_players(name)
        return {"players": players}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/players/game/{game_id}")
def get_game_players_route(game_id: int):
    """Get all players from both teams in a specific game"""
    try:
        sds = SportsDataService()
        players = sds.get_game_players(str(game_id))
        return {"players": players}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/odds/week/{week}")
def get_week_odds_route(week: int, season: str = "2025REG"):
    """Get betting odds for a specific week"""
    try:
        sds = SportsDataService()
        odds = sds.get_game_odds(season)
        return {"odds": odds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/odds/game/{game_id}")
def get_game_odds_route(game_id: int):
    """Get betting odds for a specific game"""
    try:
        sds = SportsDataService()
        odds = sds.get_pregame_odds(game_id)
        return {"odds": odds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/odds/live/{game_id}")
def get_live_odds_route(game_id: int):
    """Get live betting odds for a specific game"""
    try:
        sds = SportsDataService()
        odds = sds.get_live_odds(game_id)
        return {"odds": odds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/odds/sportsbooks")
def get_sportsbook_odds_route(season: str = "2025REG"):
    """Get odds from multiple sportsbooks"""
    try:
        sds = SportsDataService()
        odds = sds.get_sportsbook_odds(season)
        return {"odds": odds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/betting/trends/{team}")
def get_betting_trends_route(team: str):
    """Get betting trends for a team"""
    try:
        sds = SportsDataService()
        trends = sds.get_betting_trends(team)
        return {"trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predictions/win/{game_id}")
def predict_game_winner_route(game_id: str):
    """Predict game winner based on betting odds and historical data"""
    try:
        sds = SportsDataService()
        
        # Get game info
        schedule = sds.get_nfl_schedule()
        game = next((g for g in schedule if g['GameKey'] == game_id), None)
        
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Try to get betting odds
        try:
            odds = sds.get_pregame_odds(game_id)
        except:
            odds = None
        
        # Basic prediction logic using point spread from schedule
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        point_spread = game.get('PointSpread', 0)
        over_under = game.get('OverUnder', 0)
        home_ml = game.get('HomeTeamMoneyLine', 0)
        away_ml = game.get('AwayTeamMoneyLine', 0)
        
        # Predict based on point spread (negative means home team favored)
        if point_spread < 0:
            predicted_winner = home_team
            confidence = min(95, abs(point_spread) * 5 + 50)  # Higher spread = higher confidence
            spread_analysis = f"Home team favored by {abs(point_spread)} points"
        elif point_spread > 0:
            predicted_winner = away_team
            confidence = min(95, abs(point_spread) * 5 + 50)
            spread_analysis = f"Away team favored by {abs(point_spread)} points"
        else:
            predicted_winner = home_team  # Home field advantage
            confidence = 55
            spread_analysis = "Even game, home field advantage"
        
        # Money line analysis
        if home_ml < 0:
            ml_favorite = home_team
            ml_analysis = f"Home team favored (ML: {home_ml})"
        elif away_ml < 0:
            ml_favorite = away_team
            ml_analysis = f"Away team favored (ML: {away_ml})"
        else:
            ml_favorite = "Even"
            ml_analysis = "Close money line odds"
        
        return {
            "game_id": game_id,
            "home_team": home_team,
            "away_team": away_team,
            "predicted_winner": predicted_winner,
            "confidence": round(confidence, 1),
            "point_spread": point_spread,
            "over_under": over_under,
            "home_money_line": home_ml,
            "away_money_line": away_ml,
            "spread_analysis": spread_analysis,
            "money_line_analysis": ml_analysis,
            "betting_recommendation": {
                "spread_pick": f"Take {predicted_winner} {'+' if point_spread > 0 else ''}{point_spread}",
                "money_line_pick": f"Take {predicted_winner} ML",
                "total_pick": f"Game total: {over_under} (analysis needed)"
            },
            "live_odds": odds if odds else "No live odds available yet"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
