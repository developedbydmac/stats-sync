"""
Halftime prediction service for generating in-game analysis and live betting opportunities
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ..models.parlay import SportType, TierType, ParlayResponse
from .sports_data_service import SportsDataService
from .oddsjam_service import OddsJamService
from .parlay_builder import ParlayBuilder
from ..utils.logger import setup_logger

logger = setup_logger()

class HalftimePredictionService:
    """Service for generating halftime/live predictions and parlays"""
    
    def __init__(self, sports_data_service: SportsDataService = None, oddsjam_service: OddsJamService = None):
        self.sports_data_service = sports_data_service or SportsDataService()
        self.oddsjam_service = oddsjam_service or OddsJamService()
        self.parlay_builder = ParlayBuilder()
        
    async def generate_halftime_predictions(
        self, 
        sport: SportType, 
        game_id: Optional[str] = None,
        tier: Optional[TierType] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive halftime predictions for live games
        
        Args:
            sport: Sport type (NFL, MLB, NBA, NHL)
            game_id: Specific game ID (if not provided, analyzes all live games)
            tier: Tier level for filtering parlays (Free, Premium, GOAT)
            
        Returns:
            Dictionary containing live predictions, parlays, and analysis
        """
        try:
            logger.info(f"Generating halftime predictions for {sport.value}")
            
            # Fetch live games and their current status
            live_games = await self._fetch_live_games(sport, game_id)
            
            if not live_games:
                logger.warning(f"No live games found for {sport.value}")
                return {
                    "predictions": {"games": [], "live_props": []},
                    "parlays": [],
                    "analysis": {"message": "No live games available"},
                    "recommendations": {}
                }
            
            # Fetch live player props and odds
            live_props = await self._fetch_live_props(sport)
            live_odds = await self._fetch_live_odds(sport)
            
            # Generate in-game analysis
            game_analysis = await self._analyze_live_games(live_games)
            
            # Generate live prop predictions
            prop_predictions = await self._analyze_live_props(live_props, live_games)
            
            # Build live betting parlays
            parlays = await self._build_halftime_parlays(prop_predictions, game_analysis, tier)
            
            # Compile real-time analysis
            analysis = {
                "sport": sport.value,
                "live_games": len(live_games),
                "live_props": len(live_props),
                "high_confidence_plays": len([p for p in prop_predictions if p.get("confidence", 0) > 80]),
                "generated_parlays": len(parlays),
                "timestamp": datetime.now().isoformat(),
                "market_conditions": await self._assess_market_conditions(live_odds)
            }
            
            return {
                "predictions": {
                    "games": game_analysis,
                    "live_props": prop_predictions
                },
                "parlays": parlays,
                "analysis": analysis,
                "recommendations": await self._generate_live_recommendations(game_analysis, prop_predictions)
            }
            
        except Exception as e:
            logger.error(f"Error generating halftime predictions: {str(e)}")
            raise
    
    async def _fetch_live_games(self, sport: SportType, game_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch currently live games"""
        try:
            if game_id:
                # Fetch specific game
                game = await self.sports_data_service.get_game_by_id(sport, game_id)
                return [game] if game else []
            else:
                # Fetch all live games
                games = await self.sports_data_service.get_live_games(sport)
                logger.info(f"Fetched {len(games)} live games for {sport.value}")
                return games
        except Exception as e:
            logger.error(f"Error fetching live games: {str(e)}")
            return []
    
    async def _fetch_live_props(self, sport: SportType) -> List[Dict[str, Any]]:
        """Fetch live player props from OddsJam"""
        try:
            props = await self.oddsjam_service.fetch_live_props(sport)
            logger.info(f"Fetched {len(props)} live props for {sport.value}")
            return props
        except Exception as e:
            logger.error(f"Error fetching live props: {str(e)}")
            return []
    
    async def _fetch_live_odds(self, sport: SportType) -> List[Dict[str, Any]]:
        """Fetch live odds data"""
        try:
            odds = await self.oddsjam_service.fetch_live_odds(sport)
            logger.info(f"Fetched live odds for {sport.value}")
            return odds
        except Exception as e:
            logger.error(f"Error fetching live odds: {str(e)}")
            return []
    
    async def _analyze_live_games(self, live_games: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze live games and generate in-game predictions"""
        predictions = []
        
        for game in live_games:
            try:
                home_team = game.get("HomeTeam", "")
                away_team = game.get("AwayTeam", "")
                home_score = game.get("HomeScore", 0)
                away_score = game.get("AwayScore", 0)
                quarter = game.get("Quarter", "")
                time_remaining = game.get("TimeRemainingMinutes", 0)
                
                # Calculate momentum and trends
                momentum = self._calculate_momentum(game)
                scoring_trend = self._analyze_scoring_trend(game)
                
                prediction = {
                    "game_id": game.get("GameID"),
                    "home_team": home_team,
                    "away_team": away_team,
                    "current_score": {"home": home_score, "away": away_score},
                    "quarter": quarter,
                    "time_remaining": time_remaining,
                    "momentum": momentum,
                    "scoring_trend": scoring_trend,
                    "live_recommendations": self._generate_live_game_recommendations(game, momentum, scoring_trend),
                    "confidence": self._calculate_live_game_confidence(game, momentum),
                    "key_factors": self._identify_live_factors(game)
                }
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Error analyzing live game: {str(e)}")
                continue
        
        return predictions
    
    async def _analyze_live_props(self, props: List[Dict], live_games: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze live player props with current game context"""
        predictions = []
        
        # Create a lookup for game context
        game_context = {game.get("GameID"): game for game in live_games}
        
        for prop in props:
            try:
                player_name = prop.get("PlayerName", "")
                prop_type = prop.get("PropType", "")
                target_value = prop.get("Target", 0)
                current_value = prop.get("CurrentValue", 0)
                game_id = prop.get("GameID")
                
                # Get game context for this prop
                game = game_context.get(game_id, {})
                
                prediction = {
                    "player_name": player_name,
                    "prop_type": prop_type,
                    "target": target_value,
                    "current_value": current_value,
                    "progress": current_value / target_value if target_value > 0 else 0,
                    "recommendation": self._generate_live_prop_recommendation(prop, game),
                    "confidence": self._calculate_live_prop_confidence(prop, game),
                    "time_factor": self._assess_time_factor(game),
                    "game_context": {
                        "quarter": game.get("Quarter", ""),
                        "time_remaining": game.get("TimeRemainingMinutes", 0),
                        "score_differential": abs(game.get("HomeScore", 0) - game.get("AwayScore", 0))
                    }
                }
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Error analyzing live prop: {str(e)}")
                continue
        
        return predictions
    
    async def _build_halftime_parlays(self, prop_predictions: List[Dict], game_analysis: List[Dict], tier: Optional[TierType]) -> List[ParlayResponse]:
        """Build optimized parlays for halftime/live betting"""
        try:
            # Filter high-confidence live predictions
            high_confidence_props = [
                p for p in prop_predictions 
                if p.get("confidence", 0) > 75  # Lower threshold for live betting
            ]
            
            high_confidence_games = [
                g for g in game_analysis
                if g.get("confidence", 0) > 75
            ]
            
            all_predictions = high_confidence_props + high_confidence_games
            
            if not all_predictions:
                logger.warning("No high-confidence live predictions available for parlay building")
                return []
            
            # Build parlays optimized for live betting
            parlays = await self.parlay_builder.build_live_parlays(all_predictions, tier)
            
            # Convert to ParlayResponse format
            parlay_responses = []
            for parlay in parlays:
                response = ParlayResponse(
                    parlay=parlay,
                    tier_requirements={"min_confidence": 75.0, "source": "halftime", "is_live": True},
                    analysis={
                        "type": "halftime_prediction", 
                        "generated_at": datetime.now().isoformat(),
                        "market_type": "live_betting"
                    }
                )
                parlay_responses.append(response)
            
            return parlay_responses
            
        except Exception as e:
            logger.error(f"Error building halftime parlays: {str(e)}")
            return []
    
    def _calculate_momentum(self, game: Dict) -> Dict[str, Any]:
        """Calculate game momentum based on recent scoring"""
        # Basic momentum calculation - can be enhanced with more data
        home_score = game.get("HomeScore", 0)
        away_score = game.get("AwayScore", 0)
        quarter = game.get("Quarter", "")
        
        # Simple momentum based on score differential and quarter
        score_diff = home_score - away_score
        
        momentum = {
            "direction": "home" if score_diff > 0 else "away" if score_diff < 0 else "neutral",
            "strength": min(abs(score_diff) / 10, 1.0),  # Normalize to 0-1
            "quarter": quarter,
            "score_differential": score_diff
        }
        
        return momentum
    
    def _analyze_scoring_trend(self, game: Dict) -> Dict[str, Any]:
        """Analyze scoring trends in the game"""
        total_score = game.get("HomeScore", 0) + game.get("AwayScore", 0)
        quarter = game.get("Quarter", "")
        
        # Basic trend analysis
        scoring_trend = {
            "total_score": total_score,
            "pace": "fast" if total_score > 100 else "normal" if total_score > 80 else "slow",
            "quarter": quarter,
            "projected_total": self._project_final_score(total_score, quarter)
        }
        
        return scoring_trend
    
    def _project_final_score(self, current_total: int, quarter: str) -> int:
        """Project final score based on current pace"""
        if quarter == "1st":
            return current_total * 4
        elif quarter == "2nd":
            return current_total * 2
        elif quarter == "3rd":
            return int(current_total * 1.33)
        else:
            return current_total
    
    def _generate_live_game_recommendations(self, game: Dict, momentum: Dict, scoring_trend: Dict) -> List[str]:
        """Generate live betting recommendations for the game"""
        recommendations = []
        
        total_score = scoring_trend["total_score"]
        pace = scoring_trend["pace"]
        momentum_direction = momentum["direction"]
        
        if pace == "fast":
            recommendations.append("Consider Over bets on remaining quarters")
        elif pace == "slow":
            recommendations.append("Consider Under bets on remaining quarters")
        
        if momentum_direction != "neutral":
            team = momentum_direction.title()
            recommendations.append(f"Consider {team} ML or spread bets")
        
        return recommendations
    
    def _calculate_live_game_confidence(self, game: Dict, momentum: Dict) -> float:
        """Calculate confidence for live game predictions"""
        base_confidence = 70.0  # Lower base for live betting
        
        # Adjust based on momentum strength
        momentum_strength = momentum.get("strength", 0)
        base_confidence += momentum_strength * 15
        
        # Adjust based on score differential
        score_diff = abs(game.get("HomeScore", 0) - game.get("AwayScore", 0))
        if score_diff > 15:
            base_confidence += 10  # High confidence in blowouts
        elif score_diff < 3:
            base_confidence -= 5   # Lower confidence in close games
        
        return min(base_confidence, 90.0)
    
    def _identify_live_factors(self, game: Dict) -> List[str]:
        """Identify key factors affecting live betting"""
        factors = []
        
        score_diff = abs(game.get("HomeScore", 0) - game.get("AwayScore", 0))
        quarter = game.get("Quarter", "")
        time_remaining = game.get("TimeRemainingMinutes", 0)
        
        if score_diff > 20:
            factors.append("Large score differential")
        elif score_diff < 3:
            factors.append("Close game")
        
        if quarter in ["4th", "OT"]:
            factors.append("Late game situation")
        
        if time_remaining < 5:
            factors.append("Limited time remaining")
        
        return factors
    
    def _generate_live_prop_recommendation(self, prop: Dict, game: Dict) -> str:
        """Generate recommendation for live player prop"""
        current_value = prop.get("CurrentValue", 0)
        target_value = prop.get("Target", 0)
        progress = current_value / target_value if target_value > 0 else 0
        
        quarter = game.get("Quarter", "")
        time_remaining = game.get("TimeRemainingMinutes", 0)
        
        # Simple recommendation logic
        if progress > 0.8:
            return "Strong Over"
        elif progress < 0.3 and quarter in ["3rd", "4th"]:
            return "Strong Under"
        elif progress > 0.6:
            return "Over"
        elif progress < 0.4:
            return "Under"
        else:
            return "Monitor"
    
    def _calculate_live_prop_confidence(self, prop: Dict, game: Dict) -> float:
        """Calculate confidence for live player prop"""
        base_confidence = 75.0
        
        current_value = prop.get("CurrentValue", 0)
        target_value = prop.get("Target", 0)
        progress = current_value / target_value if target_value > 0 else 0
        
        quarter = game.get("Quarter", "")
        
        # Adjust confidence based on progress and time
        if progress > 0.8:
            base_confidence += 15
        elif progress < 0.2 and quarter in ["3rd", "4th"]:
            base_confidence += 10
        elif 0.4 <= progress <= 0.6:
            base_confidence -= 10  # Uncertain middle ground
        
        return max(min(base_confidence, 95.0), 60.0)
    
    def _assess_time_factor(self, game: Dict) -> Dict[str, Any]:
        """Assess how time remaining affects prop likelihood"""
        quarter = game.get("Quarter", "")
        time_remaining = game.get("TimeRemainingMinutes", 0)
        
        if quarter == "4th" and time_remaining < 5:
            urgency = "High"
            factor = "Limited time remaining"
        elif quarter in ["3rd", "4th"]:
            urgency = "Medium"
            factor = "Late game context"
        else:
            urgency = "Low"
            factor = "Plenty of time remaining"
        
        return {
            "urgency": urgency,
            "factor": factor,
            "quarter": quarter,
            "minutes_remaining": time_remaining
        }
    
    async def _assess_market_conditions(self, live_odds: List[Dict]) -> Dict[str, Any]:
        """Assess current market conditions for live betting"""
        if not live_odds:
            return {"status": "No live odds available"}
        
        # Basic market assessment
        total_markets = len(live_odds)
        
        return {
            "total_markets": total_markets,
            "market_status": "Active" if total_markets > 0 else "Limited",
            "liquidity": "High" if total_markets > 50 else "Medium" if total_markets > 20 else "Low",
            "recommendation": "Favorable for live betting" if total_markets > 30 else "Limited opportunities"
        }
    
    async def _generate_live_recommendations(self, game_analysis: List[Dict], prop_predictions: List[Dict]) -> Dict[str, Any]:
        """Generate overall live betting recommendations"""
        high_confidence_games = [g for g in game_analysis if g.get("confidence", 0) > 80]
        high_confidence_props = [p for p in prop_predictions if p.get("confidence", 0) > 80]
        
        # Calculate urgency based on game states
        urgent_plays = []
        for game in game_analysis:
            quarter = game.get("quarter", "")
            if quarter in ["4th", "OT"]:
                urgent_plays.extend(game.get("live_recommendations", []))
        
        return {
            "top_live_games": high_confidence_games[:2],
            "top_live_props": high_confidence_props[:3],
            "urgent_plays": urgent_plays,
            "betting_strategy": {
                "approach": "Conservative" if len(high_confidence_props) < 3 else "Aggressive",
                "bankroll_allocation": "20-30% for live betting",
                "time_sensitivity": "High - live odds change rapidly"
            },
            "market_timing": "Optimal for immediate action" if urgent_plays else "Monitor for opportunities"
        }
