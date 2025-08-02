"""
SportsDataIO service for fetching player stats and game logs
"""
import aiohttp
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from models.parlay_schema import SportType, PropType, PlayerStats, GameLog, PlayerAnalysis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SportsDataIOService:
    """Service for fetching data from SportsDataIO API"""
    
    def __init__(self):
        self.api_key = os.getenv("SPORTSDATAIO_API_KEY")
        self.base_url = "https://api.sportsdata.io/v3"
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            raise ValueError("SPORTSDATAIO_API_KEY environment variable is required")
        
        logger.info(f"SportsDataIO API key configured: {self.api_key[:8]}...")
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            
            # Create SSL context that's more permissive for development
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self.session
    
    async def close_session(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_player_game_logs(
        self, 
        sport: SportType, 
        player_name: str = None,
        team: str = None,
        position: str = None,
        days_back: int = 10
    ) -> List[PlayerStats]:
        """
        Get player game logs from SportsDataIO
        
        Args:
            sport: Sport type (MLB, NFL, NBA, NHL)
            player_name: Optional specific player name
            team: Optional team filter
            position: Optional position filter
            days_back: Number of days to look back
            
        Returns:
            List of PlayerStats objects
        """
        try:
            session = await self.get_session()
            sport_key = self._get_sport_key(sport)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Get games in date range
            games_url = f"{self.base_url}/{sport_key}/scores/json/GamesByDate/{end_date.strftime('%Y-%m-%d')}"
            
            params = {"key": self.api_key}
            
            logger.info(f"Fetching game logs from: {games_url}")
            
            async with session.get(games_url, params=params) as response:
                if response.status == 200:
                    games_data = await response.json()
                    
                    # Get player stats for each game
                    all_player_stats = []
                    
                    for game in games_data:
                        game_date = game.get("Date", "")[:10]  # YYYY-MM-DD format
                        
                        # Get box score for this game
                        box_score_url = f"{self.base_url}/{sport_key}/stats/json/BoxScore/{game.get('GameID')}"
                        
                        try:
                            async with session.get(box_score_url, params=params) as box_response:
                                if box_response.status == 200:
                                    box_data = await box_response.json()
                                    player_stats = self._extract_player_stats(box_data, sport, game_date)
                                    
                                    # Apply filters
                                    filtered_stats = self._apply_filters(
                                        player_stats, player_name, team, position
                                    )
                                    
                                    all_player_stats.extend(filtered_stats)
                                    
                        except Exception as e:
                            logger.warning(f"Error fetching box score for game {game.get('GameID')}: {e}")
                            continue
                    
                    logger.info(f"Retrieved {len(all_player_stats)} player game logs")
                    return all_player_stats
                    
                else:
                    error_text = await response.text()
                    logger.error(f"SportsDataIO API error {response.status}: {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching player game logs: {str(e)}")
            return []
    
    async def get_recent_player_props(
        self, 
        sport: SportType, 
        min_hit_rate: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Get recent high-hit-rate player props
        
        Args:
            sport: Sport type
            min_hit_rate: Minimum hit rate threshold
            
        Returns:
            List of player prop data with estimated odds
        """
        try:
            # Try to get real data first
            player_stats = await self.get_player_game_logs(sport, days_back=10)
            
            if not player_stats:
                # If no real data available, use mock data for testing
                logger.warning(f"No real data available for {sport.value}, using mock data")
                return self._get_mock_player_props(sport, min_hit_rate)
            
            # Calculate hit rates for different prop types
            props_with_rates = []
            
            for player_stat in player_stats:
                analysis = await self.analyze_player_performance(player_stat.player_name, sport)
                
                # Generate props for different stat types
                for prop_type, hit_rate in analysis.prop_hit_rates.items():
                    if hit_rate >= min_hit_rate:
                        prop_data = {
                            "player_name": player_stat.player_name,
                            "team": player_stat.team,
                            "prop_type": prop_type.value,
                            "hit_rate": hit_rate,
                            "confidence_score": hit_rate * 100,
                            "recent_form": self._get_recent_form(analysis.recent_games, prop_type),
                            "game_date": player_stat.game_date,
                            "position": player_stat.position
                        }
                        props_with_rates.append(prop_data)
            
            # Sort by hit rate (highest first)
            props_with_rates.sort(key=lambda x: x["hit_rate"], reverse=True)
            
            logger.info(f"Found {len(props_with_rates)} high-hit-rate props")
            return props_with_rates
            
        except Exception as e:
            logger.error(f"Error getting recent player props: {str(e)}")
            logger.info(f"Falling back to mock data for {sport.value}")
            return self._get_mock_player_props(sport, min_hit_rate)
    
    async def analyze_player_performance(self, player_name: str, sport: SportType) -> PlayerAnalysis:
        """
        Analyze player performance and calculate prop hit rates
        
        Args:
            player_name: Player name
            sport: Sport type
            
        Returns:
            PlayerAnalysis object
        """
        try:
            # Get player's recent game logs
            player_stats = await self.get_player_game_logs(sport, player_name=player_name, days_back=20)
            
            # Convert to GameLog objects
            recent_games = []
            for stat in player_stats:
                game_log = GameLog(
                    date=stat.game_date,
                    opponent="",  # Would need opponent lookup
                    stats=stat.stats
                )
                recent_games.append(game_log)
            
            # Calculate hit rates for different prop types
            prop_hit_rates = {}
            
            if sport == SportType.MLB:
                prop_hit_rates = self._calculate_mlb_hit_rates(recent_games)
            elif sport == SportType.NFL:
                prop_hit_rates = self._calculate_nfl_hit_rates(recent_games)
            elif sport == SportType.NBA:
                prop_hit_rates = self._calculate_nba_hit_rates(recent_games)
            
            # Determine if trending up
            trending_up = self._is_trending_up(recent_games)
            
            # Basic confidence factors
            confidence_factors = {
                "recent_form": 0.8 if trending_up else 0.6,
                "consistency": self._calculate_consistency(recent_games),
                "injury_status": 1.0  # Would need injury data integration
            }
            
            return PlayerAnalysis(
                player_name=player_name,
                recent_games=recent_games,
                prop_hit_rates=prop_hit_rates,
                trending_up=trending_up,
                injury_status="healthy",  # Would need real injury data
                confidence_factors=confidence_factors
            )
            
        except Exception as e:
            logger.error(f"Error analyzing player performance: {str(e)}")
            return PlayerAnalysis(
                player_name=player_name,
                recent_games=[],
                prop_hit_rates={},
                trending_up=False,
                injury_status="unknown",
                confidence_factors={}
            )
    
    def _get_sport_key(self, sport: SportType) -> str:
        """Map SportType to SportsDataIO API keys"""
        sport_mapping = {
            SportType.MLB: "mlb",
            SportType.NFL: "nfl",
            SportType.NBA: "nba", 
            SportType.NHL: "nhl"
        }
        return sport_mapping.get(sport, "mlb")
    
    def _extract_player_stats(self, box_data: Dict, sport: SportType, game_date: str) -> List[PlayerStats]:
        """Extract player stats from box score data"""
        player_stats = []
        
        try:
            if sport == SportType.MLB:
                # Extract hitting stats
                for team_key in ["AwayTeam", "HomeTeam"]:
                    if team_key in box_data and "PlayerGames" in box_data[team_key]:
                        for player in box_data[team_key]["PlayerGames"]:
                            if player.get("PositionCategory") == "Hitter":
                                stats = {
                                    "hits": player.get("Hits", 0),
                                    "home_runs": player.get("HomeRuns", 0),
                                    "rbis": player.get("RunsBattedIn", 0),
                                    "strikeouts": player.get("Strikeouts", 0),
                                    "at_bats": player.get("AtBats", 0)
                                }
                                
                                player_stat = PlayerStats(
                                    player_name=player.get("Name", ""),
                                    team=player.get("Team", ""),
                                    position=player.get("Position", ""),
                                    game_date=game_date,
                                    stats=stats
                                )
                                player_stats.append(player_stat)
            
            elif sport == SportType.NFL:
                # Extract NFL stats (passing, rushing, receiving)
                for team_key in ["AwayTeam", "HomeTeam"]:
                    if team_key in box_data and "PlayerGames" in box_data[team_key]:
                        for player in box_data[team_key]["PlayerGames"]:
                            stats = {
                                "passing_yards": player.get("PassingYards", 0),
                                "rushing_yards": player.get("RushingYards", 0),
                                "receiving_yards": player.get("ReceivingYards", 0),
                                "receptions": player.get("Receptions", 0),
                                "touchdowns": player.get("Touchdowns", 0)
                            }
                            
                            player_stat = PlayerStats(
                                player_name=player.get("Name", ""),
                                team=player.get("Team", ""),
                                position=player.get("Position", ""),
                                game_date=game_date,
                                stats=stats
                            )
                            player_stats.append(player_stat)
            
        except Exception as e:
            logger.warning(f"Error extracting player stats: {e}")
        
        return player_stats
    
    def _apply_filters(
        self, 
        player_stats: List[PlayerStats], 
        player_name: str = None,
        team: str = None, 
        position: str = None
    ) -> List[PlayerStats]:
        """Apply filters to player stats"""
        filtered = player_stats
        
        if player_name:
            filtered = [p for p in filtered if player_name.lower() in p.player_name.lower()]
        
        if team:
            filtered = [p for p in filtered if team.upper() in p.team.upper()]
        
        if position:
            filtered = [p for p in filtered if position.upper() in p.position.upper()]
        
        return filtered
    
    def _calculate_mlb_hit_rates(self, recent_games: List[GameLog]) -> Dict[PropType, float]:
        """Calculate MLB prop hit rates"""
        hit_rates = {}
        
        if not recent_games:
            return hit_rates
        
        # Calculate hit rates for common MLB props
        hits_over_0_5 = sum(1 for game in recent_games if game.stats.get("hits", 0) >= 1)
        home_runs_over_0_5 = sum(1 for game in recent_games if game.stats.get("home_runs", 0) >= 1) 
        rbis_over_0_5 = sum(1 for game in recent_games if game.stats.get("rbis", 0) >= 1)
        
        total_games = len(recent_games)
        
        hit_rates[PropType.HITS] = hits_over_0_5 / total_games
        hit_rates[PropType.HOME_RUNS] = home_runs_over_0_5 / total_games
        hit_rates[PropType.RBIS] = rbis_over_0_5 / total_games
        
        return hit_rates
    
    def _calculate_nfl_hit_rates(self, recent_games: List[GameLog]) -> Dict[PropType, float]:
        """Calculate NFL prop hit rates"""
        hit_rates = {}
        
        if not recent_games:
            return hit_rates
        
        # Calculate hit rates for common NFL props
        passing_over_250 = sum(1 for game in recent_games if game.stats.get("passing_yards", 0) >= 250)
        rushing_over_50 = sum(1 for game in recent_games if game.stats.get("rushing_yards", 0) >= 50)
        receiving_over_50 = sum(1 for game in recent_games if game.stats.get("receiving_yards", 0) >= 50)
        
        total_games = len(recent_games)
        
        hit_rates[PropType.PASSING_YARDS] = passing_over_250 / total_games
        hit_rates[PropType.RUSHING_YARDS] = rushing_over_50 / total_games  
        hit_rates[PropType.RECEIVING_YARDS] = receiving_over_50 / total_games
        
        return hit_rates
    
    def _calculate_nba_hit_rates(self, recent_games: List[GameLog]) -> Dict[PropType, float]:
        """Calculate NBA prop hit rates"""
        hit_rates = {}
        
        if not recent_games:
            return hit_rates
        
        # Calculate hit rates for common NBA props
        points_over_20 = sum(1 for game in recent_games if game.stats.get("points", 0) >= 20)
        assists_over_5 = sum(1 for game in recent_games if game.stats.get("assists", 0) >= 5)
        rebounds_over_8 = sum(1 for game in recent_games if game.stats.get("rebounds", 0) >= 8)
        
        total_games = len(recent_games)
        
        hit_rates[PropType.POINTS] = points_over_20 / total_games
        hit_rates[PropType.ASSISTS] = assists_over_5 / total_games
        hit_rates[PropType.REBOUNDS] = rebounds_over_8 / total_games
        
        return hit_rates
    
    def _get_recent_form(self, recent_games: List[GameLog], prop_type: PropType) -> List[bool]:
        """Get recent form (hits/misses) for a prop type"""
        form = []
        
        for game in recent_games[-10:]:  # Last 10 games
            if prop_type == PropType.HITS:
                hit = game.stats.get("hits", 0) >= 1
            elif prop_type == PropType.HOME_RUNS:
                hit = game.stats.get("home_runs", 0) >= 1
            elif prop_type == PropType.RBIS:
                hit = game.stats.get("rbis", 0) >= 1
            elif prop_type == PropType.PASSING_YARDS:
                hit = game.stats.get("passing_yards", 0) >= 250
            else:
                hit = False  # Default
            
            form.append(hit)
        
        return form
    
    def _is_trending_up(self, recent_games: List[GameLog]) -> bool:
        """Determine if player is trending up based on recent performance"""
        if len(recent_games) < 6:
            return False
        
        # Compare first half vs second half of recent games
        mid_point = len(recent_games) // 2
        first_half = recent_games[:mid_point]
        second_half = recent_games[mid_point:]
        
        # Calculate average performance (simplified)
        first_avg = sum(sum(game.stats.values()) for game in first_half) / len(first_half)
        second_avg = sum(sum(game.stats.values()) for game in second_half) / len(second_half)
        
        return second_avg > first_avg
    
    def _calculate_consistency(self, recent_games: List[GameLog]) -> float:
        """Calculate consistency score (0-1) based on performance variance"""
        if len(recent_games) < 3:
            return 0.5
        
        # Calculate variance in total stats per game
        total_stats = [sum(game.stats.values()) for game in recent_games]
        avg_stats = sum(total_stats) / len(total_stats)
        
        variance = sum((stat - avg_stats) ** 2 for stat in total_stats) / len(total_stats)
        
        # Convert variance to consistency score (lower variance = higher consistency)
        consistency = max(0.0, min(1.0, 1.0 - (variance / (avg_stats + 1))))
        
        return consistency
    
    def _get_mock_player_props(self, sport: SportType, min_hit_rate: float) -> List[Dict[str, Any]]:
        """Generate mock player props for testing when API is unavailable"""
        mock_props = []
        
        if sport == SportType.MLB:
            # Mock MLB players and props
            mlb_players = [
                {"name": "Aaron Judge", "team": "NYY", "position": "OF"},
                {"name": "Mookie Betts", "team": "LAD", "position": "OF"},
                {"name": "Ronald Acuña Jr.", "team": "ATL", "position": "OF"},
                {"name": "Juan Soto", "team": "SD", "position": "OF"},
                {"name": "Vladimir Guerrero Jr.", "team": "TOR", "position": "1B"},
                {"name": "Fernando Tatis Jr.", "team": "SD", "position": "SS"},
                {"name": "Freddie Freeman", "team": "LAD", "position": "1B"},
                {"name": "Yordan Alvarez", "team": "HOU", "position": "DH"},
            ]
            
            prop_types = [PropType.HITS, PropType.HOME_RUNS, PropType.RBIS, PropType.STRIKEOUTS]
            
            for player in mlb_players:
                for prop_type in prop_types:
                    # Generate realistic hit rates
                    if prop_type == PropType.HITS:
                        hit_rate = 0.75 + (hash(player["name"] + prop_type.value) % 20) / 100  # 0.75-0.94
                    elif prop_type == PropType.HOME_RUNS:
                        hit_rate = 0.15 + (hash(player["name"] + prop_type.value) % 15) / 100  # 0.15-0.29
                    elif prop_type == PropType.RBIS:
                        hit_rate = 0.45 + (hash(player["name"] + prop_type.value) % 25) / 100  # 0.45-0.69
                    else:  # STRIKEOUTS
                        hit_rate = 0.25 + (hash(player["name"] + prop_type.value) % 20) / 100  # 0.25-0.44
                    
                    if hit_rate >= min_hit_rate:
                        mock_props.append({
                            "player_name": player["name"],
                            "team": player["team"],
                            "prop_type": prop_type.value,
                            "hit_rate": hit_rate,
                            "confidence_score": hit_rate * 100,
                            "recent_form": [True] * int(hit_rate * 10) + [False] * (10 - int(hit_rate * 10)),
                            "game_date": "2025-08-01",
                            "position": player["position"]
                        })
        
        elif sport == SportType.NFL:
            # Mock NFL players and props
            nfl_players = [
                {"name": "Josh Allen", "team": "BUF", "position": "QB"},
                {"name": "Patrick Mahomes", "team": "KC", "position": "QB"},
                {"name": "Lamar Jackson", "team": "BAL", "position": "QB"},
                {"name": "Derrick Henry", "team": "TEN", "position": "RB"},
                {"name": "Cooper Kupp", "team": "LAR", "position": "WR"},
                {"name": "Davante Adams", "team": "LV", "position": "WR"},
                {"name": "Travis Kelce", "team": "KC", "position": "TE"},
                {"name": "Saquon Barkley", "team": "NYG", "position": "RB"},
            ]
            
            prop_types = [PropType.PASSING_YARDS, PropType.RUSHING_YARDS, PropType.RECEIVING_YARDS, PropType.RECEPTIONS, PropType.TOUCHDOWNS]
            
            for player in nfl_players:
                for prop_type in prop_types:
                    # Generate realistic hit rates based on position and prop
                    base_rate = 0.6
                    if player["position"] == "QB" and prop_type == PropType.PASSING_YARDS:
                        base_rate = 0.8
                    elif player["position"] == "RB" and prop_type == PropType.RUSHING_YARDS:
                        base_rate = 0.75
                    elif player["position"] in ["WR", "TE"] and prop_type in [PropType.RECEIVING_YARDS, PropType.RECEPTIONS]:
                        base_rate = 0.7
                    
                    hit_rate = base_rate + (hash(player["name"] + prop_type.value) % 15) / 100
                    
                    if hit_rate >= min_hit_rate:
                        mock_props.append({
                            "player_name": player["name"],
                            "team": player["team"],
                            "prop_type": prop_type.value,
                            "hit_rate": hit_rate,
                            "confidence_score": hit_rate * 100,
                            "recent_form": [True] * int(hit_rate * 10) + [False] * (10 - int(hit_rate * 10)),
                            "game_date": "2025-08-01",
                            "position": player["position"]
                        })
        
        # Sort by hit rate (highest first) and limit results
        mock_props.sort(key=lambda x: x["hit_rate"], reverse=True)
        selected_props = mock_props[:15]  # Limit to 15 props for reasonable parlay generation
        
        logger.info(f"Generated {len(selected_props)} mock props for {sport.value}")
        return selected_props
