import aiohttp
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from src.models.parlay import SportType, PropType, PlayerProp
from src.utils.logger import setup_logger

logger = setup_logger()

class SportsDataService:
    """Service for fetching real-time player prop data from SportsDataIO API"""
    
    def __init__(self):
        self.api_key = os.getenv("SPORTSDATAIO_API_KEY")
        self.base_url = os.getenv("SPORTSDATAIO_BASE_URL", "https://api.sportsdata.io/v3")
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("SPORTSDATAIO_API_KEY not found in environment variables")
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper configuration"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Ocp-Apim-Subscription-Key": self.api_key or "demo_key",
                    "Content-Type": "application/json"
                }
            )
        return self.session
    
    async def close_session(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_player_props(self, sport: SportType, date: str = None) -> List[Dict[str, Any]]:
        """
        Fetch real-time player props for a given sport and date
        
        Args:
            sport: Sport type (MLB or NFL)
            date: Optional date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            List of player prop data
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            if not self.api_key or self.api_key == "demo_key":
                logger.info(f"Using mock data for {sport.value} props on {date}")
                return await self._get_mock_props(sport, date)
            
            session = await self.get_session()
            endpoint = self._get_props_endpoint(sport, date)
            
            async with session.get(endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched {len(data)} props for {sport.value} on {date}")
                    return data
                else:
                    logger.error(f"API request failed with status {response.status}")
                    return await self._get_mock_props(sport, date)
                    
        except Exception as e:
            logger.error(f"Error fetching player props: {str(e)}")
            return await self._get_mock_props(sport, date)
    
    def _get_props_endpoint(self, sport: SportType, date: str) -> str:
        """Get the appropriate API endpoint for the sport"""
        if sport == SportType.NFL:
            return f"{self.base_url}/nfl/odds/{date}/playerprop"
        elif sport == SportType.MLB:
            return f"{self.base_url}/mlb/odds/{date}/playerprop"
        else:
            raise ValueError(f"Unsupported sport: {sport}")
    
    async def _get_mock_props(self, sport: SportType, date: str) -> List[Dict[str, Any]]:
        """Generate mock prop data for development/demo purposes"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        if sport == SportType.NFL:
            return [
                {
                    "player_name": "Josh Allen",
                    "team": "BUF",
                    "opponent": "MIA",
                    "prop_type": "passing_yards",
                    "line": 275.5,
                    "over_odds": -110,
                    "under_odds": -110,
                    "game_date": date,
                    "position": "QB"
                },
                {
                    "player_name": "Stefon Diggs",
                    "team": "BUF",
                    "opponent": "MIA",
                    "prop_type": "receiving_yards",
                    "line": 85.5,
                    "over_odds": -115,
                    "under_odds": -105,
                    "game_date": date,
                    "position": "WR"
                },
                {
                    "player_name": "Derrick Henry",
                    "team": "BAL",
                    "opponent": "CIN",
                    "prop_type": "rushing_yards",
                    "line": 95.5,
                    "over_odds": -120,
                    "under_odds": +100,
                    "game_date": date,
                    "position": "RB"
                },
                {
                    "player_name": "Lamar Jackson",
                    "team": "BAL",
                    "opponent": "CIN",
                    "prop_type": "passing_yards",
                    "line": 225.5,
                    "over_odds": -105,
                    "under_odds": -115,
                    "game_date": date,
                    "position": "QB"
                },
                {
                    "player_name": "Travis Kelce",
                    "team": "KC",
                    "opponent": "LV",
                    "prop_type": "receiving_yards",
                    "line": 65.5,
                    "over_odds": -110,
                    "under_odds": -110,
                    "game_date": date,
                    "position": "TE"
                },
                {
                    "player_name": "Patrick Mahomes",
                    "team": "KC",
                    "opponent": "LV",
                    "prop_type": "passing_yards",
                    "line": 285.5,
                    "over_odds": -108,
                    "under_odds": -112,
                    "game_date": date,
                    "position": "QB"
                },
                {
                    "player_name": "Cooper Kupp",
                    "team": "LAR",
                    "opponent": "SF",
                    "prop_type": "receptions",
                    "line": 6.5,
                    "over_odds": -105,
                    "under_odds": -115,
                    "game_date": date,
                    "position": "WR"
                },
                {
                    "player_name": "Christian McCaffrey",
                    "team": "SF",
                    "opponent": "LAR",
                    "prop_type": "rushing_yards",
                    "line": 110.5,
                    "over_odds": -110,
                    "under_odds": -110,
                    "game_date": date,
                    "position": "RB"
                },
                # Additional props for better tier coverage
                {
                    "player_name": "Tyreek Hill",
                    "team": "MIA",
                    "opponent": "BUF", 
                    "prop_type": "receiving_yards",
                    "line": 75.5,
                    "over_odds": -105,
                    "under_odds": -115,
                    "game_date": date,
                    "position": "WR"
                },
                {
                    "player_name": "Justin Jefferson",
                    "team": "MIN",
                    "opponent": "GB",
                    "prop_type": "receptions",
                    "line": 6.5,
                    "over_odds": -108,
                    "under_odds": -112,
                    "game_date": date,
                    "position": "WR"
                },
                {
                    "player_name": "Saquon Barkley",
                    "team": "NYG",
                    "opponent": "DAL",
                    "prop_type": "rushing_yards",
                    "line": 85.5,
                    "over_odds": -110,
                    "under_odds": -110,
                    "game_date": date,
                    "position": "RB"
                },
                {
                    "player_name": "Dak Prescott",
                    "team": "DAL",
                    "opponent": "NYG",
                    "prop_type": "passing_touchdowns",
                    "line": 1.5,
                    "over_odds": -115,
                    "under_odds": -105,
                    "game_date": date,
                    "position": "QB"
                },
                {
                    "player_name": "CeeDee Lamb",
                    "team": "DAL",
                    "opponent": "NYG",
                    "prop_type": "receiving_yards",
                    "line": 80.5,
                    "over_odds": -108,
                    "under_odds": -112,
                    "game_date": date,
                    "position": "WR"
                },
                {
                    "player_name": "Aaron Rodgers",
                    "team": "NYJ", 
                    "opponent": "NE",
                    "prop_type": "passing_yards",
                    "line": 245.5,
                    "over_odds": -110,
                    "under_odds": -110,
                    "game_date": date,
                    "position": "QB"
                },
                {
                    "player_name": "Davante Adams",
                    "team": "LV",
                    "opponent": "KC", 
                    "prop_type": "receptions",
                    "line": 7.5,
                    "over_odds": -120,
                    "under_odds": +100,
                    "game_date": date,
                    "position": "WR"
                }
            ]
        
        elif sport == SportType.MLB:
            return [
                {
                    "player_name": "Aaron Judge",
                    "team": "NYY",
                    "opponent": "BOS",
                    "prop_type": "home_runs",
                    "line": 0.5,
                    "over_odds": +180,
                    "under_odds": -220,
                    "game_date": date,
                    "position": "OF"
                },
                {
                    "player_name": "Mookie Betts",
                    "team": "LAD",
                    "opponent": "SD",
                    "prop_type": "hits",
                    "line": 1.5,
                    "over_odds": -115,
                    "under_odds": -105,
                    "game_date": date,
                    "position": "OF"
                },
                {
                    "player_name": "Ronald Acuña Jr.",
                    "team": "ATL",
                    "opponent": "NYM",
                    "prop_type": "hits",
                    "line": 1.5,
                    "over_odds": -120,
                    "under_odds": +100,
                    "game_date": date,
                    "position": "OF"
                },
                {
                    "player_name": "Gerrit Cole",
                    "team": "NYY",
                    "opponent": "BOS",
                    "prop_type": "strikeouts",
                    "line": 7.5,
                    "over_odds": -105,
                    "under_odds": -115,
                    "game_date": date,
                    "position": "P"
                },
                {
                    "player_name": "Freddie Freeman",
                    "team": "LAD",
                    "opponent": "SD",
                    "prop_type": "rbis",
                    "line": 1.5,
                    "over_odds": +140,
                    "under_odds": -170,
                    "game_date": date,
                    "position": "1B"
                },
                # Additional MLB props for better coverage
                {
                    "player_name": "Vladimir Guerrero Jr.",
                    "team": "TOR",
                    "opponent": "TB",
                    "prop_type": "total_bases",
                    "line": 2.5,
                    "over_odds": -105,
                    "under_odds": -115,
                    "game_date": date,
                    "position": "1B"
                },
                {
                    "player_name": "Juan Soto",
                    "team": "SD",
                    "opponent": "LAD",
                    "prop_type": "hits",
                    "line": 1.5,
                    "over_odds": -108,
                    "under_odds": -112,
                    "game_date": date,
                    "position": "OF"
                },
                {
                    "player_name": "Shane Bieber",
                    "team": "CLE",
                    "opponent": "DET",
                    "prop_type": "strikeouts",
                    "line": 8.5,
                    "over_odds": -110,
                    "under_odds": -110,
                    "game_date": date,
                    "position": "P"
                },
                {
                    "player_name": "Pete Alonso",
                    "team": "NYM",
                    "opponent": "ATL",
                    "prop_type": "home_runs",
                    "line": 0.5,
                    "over_odds": +150,
                    "under_odds": -180,
                    "game_date": date,
                    "position": "1B"
                },
                {
                    "player_name": "Kyle Tucker",
                    "team": "HOU",
                    "opponent": "SEA",
                    "prop_type": "hits",
                    "line": 1.5,
                    "over_odds": -115,
                    "under_odds": -105,
                    "game_date": date,
                    "position": "OF"
                },
                {
                    "player_name": "Fernando Tatis Jr.",
                    "team": "SD",
                    "opponent": "LAD",
                    "prop_type": "total_bases",
                    "line": 2.5,
                    "over_odds": +110,
                    "under_odds": -130,
                    "game_date": date,
                    "position": "SS"
                }
            ]
        
        return []
    
    async def fetch_injury_report(self, sport: SportType) -> List[Dict[str, Any]]:
        """Fetch current injury report for a sport"""
        try:
            if not self.api_key or self.api_key == "demo_key":
                return await self._get_mock_injuries(sport)
            
            session = await self.get_session()
            endpoint = self._get_injury_endpoint(sport)
            
            async with session.get(endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched injury data for {sport.value}")
                    return data
                else:
                    return await self._get_mock_injuries(sport)
                    
        except Exception as e:
            logger.error(f"Error fetching injury report: {str(e)}")
            return await self._get_mock_injuries(sport)
    
    def _get_injury_endpoint(self, sport: SportType) -> str:
        """Get the injury report endpoint for the sport"""
        if sport == SportType.NFL:
            return f"{self.base_url}/nfl/injuries"
        elif sport == SportType.MLB:
            return f"{self.base_url}/mlb/injuries"
        else:
            raise ValueError(f"Unsupported sport: {sport}")
    
    async def _get_mock_injuries(self, sport: SportType) -> List[Dict[str, Any]]:
        """Generate mock injury data"""
        await asyncio.sleep(0.1)
        
        if sport == SportType.NFL:
            return [
                {"player_name": "Travis Kelce", "status": "Questionable", "injury": "Ankle"},
                {"player_name": "Cooper Kupp", "status": "Probable", "injury": "Knee"}
            ]
        elif sport == SportType.MLB:
            return [
                {"player_name": "Aaron Judge", "status": "Day-to-Day", "injury": "Wrist"},
                {"player_name": "Mookie Betts", "status": "Healthy", "injury": None}
            ]
        
        return []
