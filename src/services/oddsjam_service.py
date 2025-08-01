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

class OddsJamService:
    """Service for fetching real player props from OddsJam API"""
    
    def __init__(self):
        self.api_key = os.getenv("ODDSJAM_API_KEY")
        self.base_url = "https://api.oddsjam.com/api/v2"
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key or self.api_key == "your_oddsjam_key_here":
            logger.warning("OddsJam API key not configured - service will return empty results")
        else:
            logger.info(f"OddsJam API key detected: {self.api_key[:8]}...")
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper configuration"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            
            # Create SSL context for secure connections
            ssl_context = ssl.create_default_context()
            
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=100,
                limit_per_host=10
            )
            
            headers = {
                "User-Agent": "StatsSync/1.0",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )
        
        return self.session
    
    async def close_session(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_player_props(self, sport: SportType, date: str = None) -> List[PlayerProp]:
        """
        Fetch real player props from OddsJam API
        
        Args:
            sport: Sport type (MLB, NFL, NBA, NHL)
            date: Optional date string (YYYY-MM-DD)
            
        Returns:
            List of PlayerProp objects with real FanDuel odds
        """
        if not self.api_key or self.api_key == "your_oddsjam_key_here":
            logger.info("OddsJam API key not configured, returning empty results")
            return []
        
        try:
            sport_key = self._get_sport_key(sport)
            session = await self.get_session()
            
            # Get player props from OddsJam
            url = f"{self.base_url}/game-odds"
            params = {
                "sport": sport_key,
                "sportsbook": "fanduel",  # Focus on FanDuel
                "market_name": "player_props",
                "is_main": "false",  # Get player props, not main markets
            }
            
            if date:
                params["date"] = date
            
            logger.info(f"Fetching OddsJam player props from: {url}")
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully fetched {len(data.get('data', []))} props from OddsJam")
                    return self._transform_oddsjam_response(data, sport)
                else:
                    error_text = await response.text()
                    logger.error(f"OddsJam API error {response.status}: {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching OddsJam player props: {str(e)}")
            return []
    
    async def fetch_live_props(self, sport: SportType) -> List[PlayerProp]:
        """
        Fetch live/in-game player props for halftime parlays
        
        Args:
            sport: Sport type
            
        Returns:
            List of PlayerProp objects for live betting
        """
        if not self.api_key or self.api_key == "your_oddsjam_key_here":
            return []
        
        try:
            sport_key = self._get_sport_key(sport)
            session = await self.get_session()
            
            url = f"{self.base_url}/live-odds"
            params = {
                "sport": sport_key,
                "sportsbook": "fanduel",
                "market_name": "player_props",
                "is_live": "true"
            }
            
            logger.info(f"Fetching live player props from OddsJam")
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    props = self._transform_oddsjam_response(data, sport)
                    logger.info(f"Successfully fetched {len(props)} live props from OddsJam")
                    return props
                else:
                    error_text = await response.text()
                    logger.error(f"OddsJam live API error {response.status}: {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching live props: {str(e)}")
            return []
    
    def _transform_oddsjam_response(self, data: Dict, sport: SportType) -> List[PlayerProp]:
        """Transform OddsJam API response to PlayerProp objects"""
        props = []
        
        for game_data in data.get("data", []):
            try:
                # Extract game info
                home_team = game_data.get("home_team", "")
                away_team = game_data.get("away_team", "")
                commence_time = game_data.get("commence_time", "")
                
                # Process player props markets
                for market in game_data.get("markets", []):
                    market_name = market.get("name", "")
                    
                    # Map OddsJam market names to our PropType
                    prop_type = self._map_market_to_prop_type(market_name, sport)
                    if not prop_type:
                        continue
                    
                    # Process each outcome (player)
                    for outcome in market.get("outcomes", []):
                        player_name = outcome.get("name", "")
                        point = outcome.get("point")
                        
                        # Get FanDuel odds specifically
                        fanduel_odds = None
                        for book in outcome.get("sportsbooks", []):
                            if book.get("sportsbook") == "fanduel":
                                fanduel_odds = book
                                break
                        
                        if not fanduel_odds:
                            continue
                        
                        # Extract over/under odds
                        over_odds = fanduel_odds.get("over_odds", -110)
                        under_odds = fanduel_odds.get("under_odds", -110)
                        
                        # Determine player team
                        team = self._determine_player_team(player_name, home_team, away_team)
                        opponent = away_team if team == home_team else home_team
                        
                        prop = PlayerProp(
                            player_name=player_name,
                            team=team[:3].upper(),
                            opponent=opponent[:3].upper(),
                            prop_type=prop_type,
                            line=float(point) if point else 0.5,
                            over_odds=over_odds,
                            under_odds=under_odds,
                            game_date=commence_time[:10] if commence_time else datetime.now().strftime("%Y-%m-%d"),
                            position="",
                            source="oddsjam_fanduel",
                            confidence_score=80.0,  # High confidence for real odds
                            hit_rate=0.55  # Will be recalculated with historical data
                        )
                        
                        props.append(prop)
                        
            except Exception as e:
                logger.warning(f"Error processing OddsJam market data: {str(e)}")
                continue
        
        logger.info(f"Transformed {len(props)} OddsJam props")
        return props
    
    def _get_sport_key(self, sport: SportType) -> str:
        """Map SportType to OddsJam sport keys"""
        sport_mapping = {
            SportType.MLB: "baseball_mlb",
            SportType.NFL: "americanfootball_nfl", 
            SportType.NBA: "basketball_nba",
            SportType.NHL: "icehockey_nhl"
        }
        return sport_mapping.get(sport, "baseball_mlb")
    
    def _map_market_to_prop_type(self, market_name: str, sport: SportType) -> Optional[PropType]:
        """Map OddsJam market names to our PropType enum"""
        market_lower = market_name.lower()
        
        if sport == SportType.MLB:
            if "hit" in market_lower:
                return PropType.HITS
            elif "rbi" in market_lower:
                return PropType.RBIS
            elif "home run" in market_lower or "homer" in market_lower:
                return PropType.HOME_RUNS
            elif "strikeout" in market_lower:
                if "pitcher" in market_lower:
                    return PropType.PITCHER_STRIKEOUTS
                else:
                    return PropType.BATTER_STRIKEOUTS
        
        elif sport == SportType.NFL:
            if "passing yard" in market_lower:
                return PropType.PASSING_YARDS
            elif "rushing yard" in market_lower:
                return PropType.RUSHING_YARDS
            elif "receiving yard" in market_lower:
                return PropType.RECEIVING_YARDS
            elif "reception" in market_lower:
                return PropType.RECEPTIONS
            elif "passing touchdown" in market_lower:
                return PropType.PASSING_TOUCHDOWNS
        
        return None
    
    def _determine_player_team(self, player_name: str, home_team: str, away_team: str) -> str:
        """
        Determine which team a player belongs to
        This is a simplified implementation - in production you'd want a roster lookup
        """
        # For now, return home team as default
        # In production, you'd implement roster lookup or player-team mapping
        return home_team
    
    async def get_available_sports(self) -> List[str]:
        """Get list of available sports from OddsJam"""
        if not self.api_key or self.api_key == "your_oddsjam_key_here":
            return []
        
        try:
            session = await self.get_session()
            url = f"{self.base_url}/sports"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    sports = [sport["key"] for sport in data.get("data", [])]
                    logger.info(f"Available sports from OddsJam: {sports}")
                    return sports
                else:
                    logger.error(f"Error fetching sports: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting available sports: {str(e)}")
            return []
