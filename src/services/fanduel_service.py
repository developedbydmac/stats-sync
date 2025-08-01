import aiohttp
import asyncio
import os
import ssl
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from src.models.parlay import SportType, PropType, PlayerProp
from src.utils.logger import setup_logger

logger = setup_logger()

class FanDuelService:
    """Service for fetching FanDuel odds via The Odds API"""
    
    def __init__(self):
        # Use a demo key for The Odds API (get from https://the-odds-api.com/)
        self.api_key = os.getenv("ODDS_API_KEY", "demo_key")
        self.base_url = "https://api.the-odds-api.com/v4"
        self.session: Optional[aiohttp.ClientSession] = None
        
        if self.api_key == "demo_key":
            logger.warning("Using demo key for The Odds API - limited to 500 requests/month")
        else:
            logger.info(f"The Odds API key detected: {self.api_key[:8]}...")
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper configuration"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            
            # Create SSL context that doesn't verify certificates (for development)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
        return self.session
    
    async def close_session(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _get_sport_key(self, sport: SportType) -> str:
        """Map our sport types to The Odds API sport keys"""
        if sport == SportType.MLB:
            return "baseball_mlb"
        elif sport == SportType.NFL:
            return "americanfootball_nfl"
        else:
            raise ValueError(f"Unsupported sport: {sport}")
    
    async def fetch_fanduel_odds(self, sport: SportType, date: str = None) -> List[PlayerProp]:
        """
        Fetch FanDuel odds from The Odds API
        
        Args:
            sport: Sport type (MLB or NFL)
            date: Optional date string (YYYY-MM-DD)
            
        Returns:
            List of PlayerProp objects with FanDuel odds
        """
        try:
            sport_key = self._get_sport_key(sport)
            session = await self.get_session()
            
            # Get today's games with FanDuel odds  
            url = f"{self.base_url}/sports/{sport_key}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "us",
                "markets": "h2h,spreads,totals",  # Standard markets available
                "bookmakers": "fanduel",
                "oddsFormat": "american",
                "dateFormat": "iso"
            }
            
            logger.info(f"Fetching FanDuel odds from: {url}")
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully fetched {len(data)} games from FanDuel")
                    return self._transform_fanduel_response(data, sport)
                else:
                    error_text = await response.text()
                    logger.error(f"FanDuel API error {response.status}: {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching FanDuel odds: {str(e)}")
            return []
    
    def _transform_fanduel_response(self, games: List[Dict], sport: SportType) -> List[PlayerProp]:
        """Transform FanDuel API response to mock player props from game data"""
        props = []
        
        logger.info(f"Processing {len(games)} games from The Odds API")
        
        for game in games:
            try:
                home_team = game.get("home_team", "")
                away_team = game.get("away_team", "")
                commence_time = game.get("commence_time", "")
                
                # Find FanDuel bookmaker data
                fanduel_data = None
                for bookmaker in game.get("bookmakers", []):
                    if bookmaker.get("key") == "fanduel":
                        fanduel_data = bookmaker
                        break
                
                if not fanduel_data:
                    continue
                    
                # Extract game totals and create mock player props
                for market in fanduel_data.get("markets", []):
                    if market.get("key") == "totals":
                        for outcome in market.get("outcomes", []):
                            total_line = outcome.get("point", 8.5)
                            odds = outcome.get("price", -110)
                            
                            # Create mock "team total hits" props based on game totals
                            # This simulates what real player props might look like
                            if sport == SportType.MLB:
                                for team, opp in [(home_team, away_team), (away_team, home_team)]:
                                    # Mock team hitting props
                                    prop = PlayerProp(
                                        player_name=f"{team} Team",
                                        team=team[:3].upper(),
                                        opponent=opp[:3].upper(),
                                        prop_type=PropType.HITS,
                                        line=round(total_line / 2.2, 1),  # Rough estimate
                                        over_odds=odds,
                                        under_odds=-130,
                                        game_date=commence_time[:10] if commence_time else datetime.now().strftime("%Y-%m-%d"),
                                        position="",
                                        source="fanduel_game_data",
                                        confidence_score=65.0,
                                        hit_rate=0.52
                                    )
                                    props.append(prop)
                        
            except Exception as e:
                logger.warning(f"Error processing FanDuel game: {str(e)}")
                continue
        
        logger.info(f"Created {len(props)} mock props from FanDuel game data")
        logger.info("Note: These are derived from game totals, not actual player props")
        logger.info("For real player props, consider upgrading to OddsJam API")
        
        return props
    
    def _map_market_to_prop_type(self, market_key: str) -> Optional[PropType]:
        """Map FanDuel market keys to our PropType enum"""
        market_mapping = {
            # MLB mappings
            "player_hits": PropType.HITS,
            "player_home_runs": PropType.HOME_RUNS,
            "player_rbis": PropType.RBIS,
            "player_strikeouts_pitcher": PropType.PITCHER_STRIKEOUTS,
            "player_strikeouts_batter": PropType.BATTER_STRIKEOUTS,
            # NFL mappings
            "player_passing_yards": PropType.PASSING_YARDS,
            "player_rushing_yards": PropType.RUSHING_YARDS,
            "player_receiving_yards": PropType.RECEIVING_YARDS,
            "player_pass_tds": PropType.PASSING_TDS,
            "player_rush_tds": PropType.RUSHING_TDS,
            "player_receptions": PropType.RECEPTIONS,
        }
        
        return market_mapping.get(market_key)
