from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import uvicorn
import os
from dotenv import load_dotenv

from pregame import pregame_prediction
from halftime import halftime_prediction
from sportsdata import SportsDataService

# Load environment variables
load_dotenv()

# Custom caching middleware for mobile performance
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Add cache headers for static content and API responses
        if request.url.path.endswith(('.css', '.js', '.png', '.jpg', '.svg')):
            response.headers["Cache-Control"] = "public, max-age=86400"  # 24 hours
        elif request.url.path.startswith('/schedule') or request.url.path.startswith('/props'):
            response.headers["Cache-Control"] = "public, max-age=300"   # 5 minutes
        elif request.url.path == '/health':
            response.headers["Cache-Control"] = "public, max-age=60"    # 1 minute
        
        return response

app = FastAPI(
    title="Stats Sync API",
    description="Sports prediction API with SportsDataIO integration",
    version="1.0.0"
)

# Add compression for mobile performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add caching middleware
app.add_middleware(CacheControlMiddleware)

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

@app.get("/ai/parlay-analysis")
def ai_parlay_analysis(risk_level: str = Query(..., description="conservative, moderate, or aggressive")):
    """AI-powered parlay analysis with specific hit rates"""
    try:
        # AI-driven hit rate targets
        hit_rates = {
            "conservative": 0.95,  # 95% hit rate
            "moderate": 0.85,      # 85% hit rate  
            "aggressive": 0.75     # 75% hit rate
        }
        
        if risk_level not in hit_rates:
            raise HTTPException(status_code=400, detail="Invalid risk level")
        
        target_hit_rate = hit_rates[risk_level]
        
        # AI Analysis (simplified for demo - would use ML models in production)
        ai_recommendations = {
            "conservative": {
                "recommended_bets": [
                    {
                        "type": "Money Line",
                        "description": "Chiefs to win vs Raiders",
                        "odds": -200,
                        "ai_confidence": 96.2,
                        "reasoning": "Chiefs 8-1 home vs Raiders, dominant offense",
                        "historical_accuracy": 94.5,
                        "key_factors": ["Home field advantage", "Quarterback advantage", "Recent form"]
                    },
                    {
                        "type": "Player Prop", 
                        "description": "Travis Kelce Over 4.5 receptions",
                        "odds": -150,
                        "ai_confidence": 97.1,
                        "reasoning": "Kelce averages 7.2 receptions, rarely under 5",
                        "historical_accuracy": 96.8,
                        "key_factors": ["Target share", "Red zone usage", "Matchup advantage"]
                    },
                    {
                        "type": "Over/Under",
                        "description": "Under 48.5 total points",
                        "odds": -110,
                        "ai_confidence": 94.8,
                        "reasoning": "Weather conditions favor under, strong defenses",
                        "historical_accuracy": 93.2,
                        "key_factors": ["Weather forecast", "Defensive rankings", "Pace of play"]
                    }
                ],
                "parlay_confidence": 89.1,  # Combined probability
                "expected_hit_rate": 95.2,
                "risk_assessment": "Very Low Risk"
            },
            "moderate": {
                "recommended_bets": [
                    {
                        "type": "Point Spread",
                        "description": "Bills -6.5 vs Jets", 
                        "odds": -110,
                        "ai_confidence": 87.3,
                        "reasoning": "Bills superior in all key metrics vs struggling Jets",
                        "historical_accuracy": 85.7,
                        "key_factors": ["Offensive efficiency", "Turnover differential", "Coaching"]
                    },
                    {
                        "type": "Player Prop",
                        "description": "Josh Allen Over 1.5 passing TDs",
                        "odds": -125,
                        "ai_confidence": 89.4,
                        "reasoning": "Allen averages 2.3 TD passes, great matchup",
                        "historical_accuracy": 88.1,
                        "key_factors": ["Red zone efficiency", "Target quality", "Game script"]
                    },
                    {
                        "type": "Player Prop",
                        "description": "Stefon Diggs Over 65.5 receiving yards", 
                        "odds": -115,
                        "ai_confidence": 86.2,
                        "reasoning": "Diggs dominates Jets secondary historically",
                        "historical_accuracy": 84.9,
                        "key_factors": ["Matchup history", "Target share", "Game flow"]
                    },
                    {
                        "type": "Over/Under",
                        "description": "Over 44.5 total points",
                        "odds": -105,
                        "ai_confidence": 83.7,
                        "reasoning": "High-scoring Bills offense vs weak Jets defense",
                        "historical_accuracy": 82.3,
                        "key_factors": ["Offensive pace", "Defensive vulnerabilities", "Weather"]
                    }
                ],
                "parlay_confidence": 68.4,
                "expected_hit_rate": 85.7,
                "risk_assessment": "Moderate Risk"
            },
            "aggressive": {
                "recommended_bets": [
                    {
                        "type": "Point Spread",
                        "description": "Cowboys -14 vs Panthers",
                        "odds": +105,
                        "ai_confidence": 78.9,
                        "reasoning": "Large spread but Cowboys desperate, Panthers rebuilding",
                        "historical_accuracy": 76.2,
                        "key_factors": ["Talent gap", "Motivation", "Home field"]
                    },
                    {
                        "type": "Player Prop",
                        "description": "Dak Prescott Over 3.5 TD passes",
                        "odds": +180,
                        "ai_confidence": 76.3,
                        "reasoning": "Dak faces weak secondary, needs big game",
                        "historical_accuracy": 74.8,
                        "key_factors": ["Matchup advantage", "Game script", "Urgency"]
                    },
                    {
                        "type": "Player Prop", 
                        "description": "CeeDee Lamb Over 125.5 receiving yards",
                        "odds": +140,
                        "ai_confidence": 74.6,
                        "reasoning": "Lamb torched similar defenses, primary target",
                        "historical_accuracy": 73.1,
                        "key_factors": ["Target share", "YAC ability", "Red zone looks"]
                    },
                    {
                        "type": "Player Prop",
                        "description": "Ezekiel Elliott Over 85.5 rushing yards",
                        "odds": +120,
                        "ai_confidence": 77.2,
                        "reasoning": "Panthers run defense ranked 28th, Cowboys will control game",
                        "historical_accuracy": 75.9,
                        "key_factors": ["Run defense ranking", "Game flow", "Volume"]
                    },
                    {
                        "type": "Over/Under",
                        "description": "Over 52.5 total points", 
                        "odds": +110,
                        "ai_confidence": 75.8,
                        "reasoning": "Cowboys offense explosive, Panthers give up points",
                        "historical_accuracy": 74.2,
                        "key_factors": ["Offensive potential", "Defensive weaknesses", "Pace"]
                    }
                ],
                "parlay_confidence": 35.7,
                "expected_hit_rate": 75.4,
                "risk_assessment": "High Risk, High Reward"
            }
        }
        
        return ai_recommendations[risk_level]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/bet-confidence/{bet_type}")
def ai_bet_confidence(bet_type: str, team: str = None, player: str = None, line: str = None):
    """Get AI confidence score for a specific bet"""
    try:
        # Simulate AI analysis based on bet parameters
        import random
        
        # Base confidence factors
        base_confidence = random.uniform(70, 85)
        
        # Adjust based on bet type
        if bet_type.lower() == "moneyline":
            confidence_boost = 10  # Money lines easier to predict
        elif bet_type.lower() == "spread":
            confidence_boost = 5   # Spreads moderate difficulty  
        elif bet_type.lower() == "total":
            confidence_boost = 3   # Totals harder to predict
        elif bet_type.lower() == "prop":
            confidence_boost = -5  # Player props most volatile
        else:
            confidence_boost = 0
            
        final_confidence = min(98, base_confidence + confidence_boost)
        
        # AI reasoning (would be from ML model in production)
        reasoning_templates = {
            "moneyline": f"Team strength analysis shows {team or 'favored team'} has significant advantages",
            "spread": f"Point differential models predict {team or 'favored team'} covers based on recent form",
            "total": f"Scoring models indicate {line or 'total'} based on pace and defensive metrics", 
            "prop": f"Player performance models show {player or 'player'} exceeds {line or 'line'} in similar matchups"
        }
        
        return {
            "confidence": round(final_confidence, 1),
            "reasoning": reasoning_templates.get(bet_type.lower(), "Statistical analysis supports this selection"),
            "key_factors": ["Historical performance", "Matchup analysis", "Recent trends"],
            "risk_level": "Low" if final_confidence > 85 else "Medium" if final_confidence > 75 else "High"
        }
        
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
