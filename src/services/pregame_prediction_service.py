"""
Pregame prediction service for generating pre-game analysis and parlays
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ..models.parlay import SportType, TierType, ParlayResponse
from .sports_data_service import SportsDataService
from .parlay_builder import ParlayBuilder
from ..utils.logger import setup_logger

logger = setup_logger()

class PregamePredictionService:
    """Service for generating pregame predictions and parlays"""
    
    def __init__(self, sports_data_service: SportsDataService = None):
        self.sports_data_service = sports_data_service or SportsDataService()
        self.parlay_builder = ParlayBuilder()
        
    async def generate_pregame_predictions(
        self, 
        sport: SportType, 
        date: Optional[str] = None,
        tier: Optional[TierType] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive pregame predictions for a given sport and date
        
        Args:
            sport: Sport type (NFL, MLB, NBA, NHL)
            date: Game date in YYYY-MM-DD format (defaults to today)
            tier: Tier level for filtering parlays (Free, Premium, GOAT)
            
        Returns:
            Dictionary containing predictions, parlays, and analysis
        """
        try:
            logger.info(f"Generating pregame predictions for {sport.value} on {date}")
            
            # Use today's date if not provided
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Fetch game schedule and player props
            games = await self._fetch_games_for_date(sport, date)
            player_props = await self._fetch_player_props(sport, date)
            team_stats = await self._fetch_team_statistics(sport)
            player_stats = await self._fetch_player_statistics(sport)
            
            # Generate game predictions
            game_predictions = await self._analyze_games(games, team_stats)
            
            # Generate player prop predictions
            prop_predictions = await self._analyze_player_props(player_props, player_stats)
            
            # Build optimized parlays
            parlays = await self._build_pregame_parlays(prop_predictions, tier)
            
            # Compile comprehensive analysis
            analysis = {
                "sport": sport.value,
                "date": date,
                "total_games": len(games),
                "total_props": len(player_props),
                "high_confidence_props": len([p for p in prop_predictions if p.get("confidence", 0) > 85]),
                "generated_parlays": len(parlays),
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "predictions": {
                    "games": game_predictions,
                    "player_props": prop_predictions
                },
                "parlays": parlays,
                "analysis": analysis,
                "recommendations": await self._generate_betting_recommendations(game_predictions, prop_predictions)
            }
            
        except Exception as e:
            logger.error(f"Error generating pregame predictions: {str(e)}")
            raise
    
    async def _fetch_games_for_date(self, sport: SportType, date: str) -> List[Dict[str, Any]]:
        """Fetch scheduled games for the given date"""
        try:
            # Convert date to the format expected by SportsDataIO
            games = await self.sports_data_service.get_games_by_date(sport, date)
            logger.info(f"Fetched {len(games)} games for {sport.value} on {date}")
            return games
        except Exception as e:
            logger.error(f"Error fetching games: {str(e)}")
            return []
    
    async def _fetch_player_props(self, sport: SportType, date: str) -> List[Dict[str, Any]]:
        """Fetch player props for the given date"""
        try:
            props = await self.sports_data_service.get_player_props(sport, date)
            logger.info(f"Fetched {len(props)} player props for {sport.value} on {date}")
            return props
        except Exception as e:
            logger.error(f"Error fetching player props: {str(e)}")
            return []
    
    async def _fetch_team_statistics(self, sport: SportType) -> Dict[str, Any]:
        """Fetch current season team statistics"""
        try:
            stats = await self.sports_data_service.get_team_stats(sport)
            logger.info(f"Fetched team statistics for {sport.value}")
            return stats
        except Exception as e:
            logger.error(f"Error fetching team stats: {str(e)}")
            return {}
    
    async def _fetch_player_statistics(self, sport: SportType) -> Dict[str, Any]:
        """Fetch current season player statistics"""
        try:
            stats = await self.sports_data_service.get_player_stats(sport)
            logger.info(f"Fetched player statistics for {sport.value}")
            return stats
        except Exception as e:
            logger.error(f"Error fetching player stats: {str(e)}")
            return {}
    
    async def _analyze_games(self, games: List[Dict], team_stats: Dict) -> List[Dict[str, Any]]:
        """Analyze games and generate predictions"""
        predictions = []
        
        for game in games:
            try:
                home_team = game.get("HomeTeam", "")
                away_team = game.get("AwayTeam", "")
                
                # Basic game analysis
                prediction = {
                    "game_id": game.get("GameID"),
                    "home_team": home_team,
                    "away_team": away_team,
                    "start_time": game.get("DateTime"),
                    "confidence": 75.0,  # Base confidence
                    "analysis": f"Pregame analysis for {away_team} @ {home_team}",
                    "recommended_bet": "Under analysis",
                    "key_factors": ["Team form", "Head-to-head record", "Injury report"]
                }
                
                # Enhanced analysis with team stats if available
                if team_stats and home_team in team_stats:
                    home_stats = team_stats[home_team]
                    away_stats = team_stats.get(away_team, {})
                    
                    # Calculate prediction confidence based on stats
                    prediction["confidence"] = self._calculate_game_confidence(home_stats, away_stats)
                    prediction["analysis"] = f"Statistical analysis: {home_team} vs {away_team}"
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Error analyzing game: {str(e)}")
                continue
        
        return predictions
    
    async def _analyze_player_props(self, props: List[Dict], player_stats: Dict) -> List[Dict[str, Any]]:
        """Analyze player props and generate predictions"""
        predictions = []
        
        for prop in props:
            try:
                player_name = prop.get("PlayerName", "")
                prop_type = prop.get("PropType", "")
                target_value = prop.get("Target", 0)
                
                prediction = {
                    "player_name": player_name,
                    "prop_type": prop_type,
                    "target": target_value,
                    "recommendation": "Over",  # Default recommendation
                    "confidence": 80.0,
                    "analysis": f"{prop_type} analysis for {player_name}",
                    "key_stats": []
                }
                
                # Enhanced analysis with player stats if available
                if player_stats and player_name in player_stats:
                    player_stat = player_stats[player_name]
                    prediction["confidence"] = self._calculate_prop_confidence(prop, player_stat)
                    prediction["key_stats"] = self._extract_relevant_stats(prop_type, player_stat)
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Error analyzing prop: {str(e)}")
                continue
        
        return predictions
    
    async def _build_pregame_parlays(self, predictions: List[Dict], tier: Optional[TierType]) -> List[ParlayResponse]:
        """Build optimized parlays from pregame predictions"""
        try:
            # Filter high-confidence predictions
            high_confidence_predictions = [
                p for p in predictions 
                if p.get("confidence", 0) > 80
            ]
            
            if not high_confidence_predictions:
                logger.warning("No high-confidence predictions available for parlay building")
                return []
            
            # Build parlays using the parlay builder
            parlays = await self.parlay_builder.build_parlays(high_confidence_predictions, tier)
            
            # Convert to ParlayResponse format
            parlay_responses = []
            for parlay in parlays:
                response = ParlayResponse(
                    parlay=parlay,
                    tier_requirements={"min_confidence": 80.0, "source": "pregame"},
                    analysis={"type": "pregame_prediction", "generated_at": datetime.now().isoformat()}
                )
                parlay_responses.append(response)
            
            return parlay_responses
            
        except Exception as e:
            logger.error(f"Error building pregame parlays: {str(e)}")
            return []
    
    def _calculate_game_confidence(self, home_stats: Dict, away_stats: Dict) -> float:
        """Calculate confidence level for game prediction"""
        # Basic confidence calculation - can be enhanced with more sophisticated models
        base_confidence = 75.0
        
        # Add confidence based on team performance metrics
        home_wins = home_stats.get("Wins", 0)
        away_wins = away_stats.get("Wins", 0)
        
        if home_wins > away_wins:
            base_confidence += 10.0
        elif away_wins > home_wins:
            base_confidence += 5.0
        
        return min(base_confidence, 95.0)
    
    def _calculate_prop_confidence(self, prop: Dict, player_stats: Dict) -> float:
        """Calculate confidence level for player prop prediction"""
        # Basic confidence calculation
        base_confidence = 80.0
        
        prop_type = prop.get("PropType", "").lower()
        target = prop.get("Target", 0)
        
        # Get relevant average from player stats
        if "points" in prop_type:
            avg = player_stats.get("PointsPerGame", 0)
        elif "rebounds" in prop_type:
            avg = player_stats.get("ReboundsPerGame", 0)
        elif "assists" in prop_type:
            avg = player_stats.get("AssistsPerGame", 0)
        else:
            return base_confidence
        
        # Adjust confidence based on how close target is to average
        if avg > 0:
            difference_ratio = abs(target - avg) / avg
            if difference_ratio < 0.1:  # Target is within 10% of average
                base_confidence += 10.0
            elif difference_ratio > 0.3:  # Target is more than 30% from average
                base_confidence -= 15.0
        
        return max(min(base_confidence, 95.0), 60.0)
    
    def _extract_relevant_stats(self, prop_type: str, player_stats: Dict) -> List[str]:
        """Extract relevant statistics for the prop type"""
        relevant_stats = []
        prop_type_lower = prop_type.lower()
        
        if "points" in prop_type_lower:
            relevant_stats.extend([
                f"PPG: {player_stats.get('PointsPerGame', 'N/A')}",
                f"FG%: {player_stats.get('FieldGoalsPercentage', 'N/A')}",
                f"Games: {player_stats.get('Games', 'N/A')}"
            ])
        elif "rebounds" in prop_type_lower:
            relevant_stats.extend([
                f"RPG: {player_stats.get('ReboundsPerGame', 'N/A')}",
                f"ORB: {player_stats.get('OffensiveRebounds', 'N/A')}",
                f"DRB: {player_stats.get('DefensiveRebounds', 'N/A')}"
            ])
        elif "assists" in prop_type_lower:
            relevant_stats.extend([
                f"APG: {player_stats.get('AssistsPerGame', 'N/A')}",
                f"TOV: {player_stats.get('Turnovers', 'N/A')}",
                f"A/TO: {player_stats.get('AssistTurnoverRatio', 'N/A')}"
            ])
        
        return relevant_stats
    
    async def _generate_betting_recommendations(self, game_predictions: List[Dict], prop_predictions: List[Dict]) -> Dict[str, Any]:
        """Generate overall betting recommendations"""
        high_confidence_games = [g for g in game_predictions if g.get("confidence", 0) > 85]
        high_confidence_props = [p for p in prop_predictions if p.get("confidence", 0) > 85]
        
        return {
            "top_game_picks": high_confidence_games[:3],
            "top_prop_picks": high_confidence_props[:5],
            "bankroll_allocation": {
                "conservative": 60,
                "moderate": 30,
                "aggressive": 10
            },
            "risk_assessment": "Medium" if len(high_confidence_props) > 3 else "Low"
        }
