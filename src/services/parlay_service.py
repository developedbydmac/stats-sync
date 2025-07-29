import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import asyncio

from src.models.parlay import (
    Parlay, PlayerProp, SportType, TierType, PropType, ParlayResponse, SystemStats
)
from src.services.sports_data_service import SportsDataService
from src.services.parlay_builder import ParlayBuilder
from src.utils.prop_analyzer import PropAnalyzer
from src.utils.logger import setup_logger

logger = setup_logger()

class ParlayService:
    """Main service for managing parlay generation and data"""
    
    def __init__(self):
        self.sports_data_service = SportsDataService()
        self.prop_analyzer = PropAnalyzer(os.getenv("PROPS_CSV_PATH", "./data/historical_props.csv"))
        self.parlay_builder = ParlayBuilder(self.prop_analyzer)
        
        # Cache for generated parlays
        self.parlay_cache: Dict[str, List[Parlay]] = {}
        self.last_refresh: Dict[str, datetime] = {}
        
        # System statistics
        self.stats = {
            "total_parlays_generated": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0
        }
    
    async def get_parlays(self, sport: SportType, tier: TierType = None) -> List[ParlayResponse]:
        """
        Get parlays for a sport and optional tier
        
        Args:
            sport: Sport type
            tier: Optional tier filter
            
        Returns:
            List of parlay responses
        """
        try:
            cache_key = f"{sport.value}_{tier.value if tier else 'all'}"
            
            # Check cache first
            if cache_key in self.parlay_cache:
                self.stats["cache_hits"] += 1
                parlays = self.parlay_cache[cache_key]
                
                # Filter by tier if specified
                if tier:
                    parlays = [p for p in parlays if p.tier == tier]
                
                # Convert to responses
                responses = [self.parlay_builder.create_parlay_response(p) for p in parlays]
                self.stats["successful_requests"] += 1
                return responses
            
            # Generate new parlays
            parlays = await self._generate_fresh_parlays(sport, tier)
            responses = [self.parlay_builder.create_parlay_response(p) for p in parlays]
            
            self.stats["successful_requests"] += 1
            return responses
            
        except Exception as e:
            logger.error(f"Error getting parlays: {str(e)}")
            self.stats["failed_requests"] += 1
            raise
    
    async def refresh_parlays(self, sport: SportType):
        """Refresh parlays for a specific sport"""
        try:
            logger.info(f"Refreshing parlays for {sport.value}")
            
            # Clear cache for this sport
            keys_to_remove = [key for key in self.parlay_cache.keys() if key.startswith(sport.value)]
            for key in keys_to_remove:
                del self.parlay_cache[key]
            
            # Generate fresh parlays for all tiers
            parlays = await self._generate_fresh_parlays(sport)
            
            # Update cache
            for tier in TierType:
                tier_parlays = [p for p in parlays if p.tier == tier]
                cache_key = f"{sport.value}_{tier.value}"
                self.parlay_cache[cache_key] = tier_parlays
            
            # Cache all parlays together
            self.parlay_cache[f"{sport.value}_all"] = parlays
            self.last_refresh[sport.value] = datetime.now()
            
            logger.info(f"Generated {len(parlays)} fresh parlays for {sport.value}")
            
        except Exception as e:
            logger.error(f"Error refreshing parlays for {sport.value}: {str(e)}")
            raise
    
    async def refresh_all_parlays(self):
        """Refresh parlays for all sports"""
        for sport in SportType:
            await self.refresh_parlays(sport)
    
    async def get_player_props(self, sport: SportType, date: str = None) -> List[Dict[str, Any]]:
        """Get raw player props data"""
        return await self.sports_data_service.fetch_player_props(sport, date)
    
    async def _generate_fresh_parlays(self, sport: SportType, tier: TierType = None) -> List[Parlay]:
        """Generate fresh parlays from current data"""
        # Fetch current props
        props_data = await self.sports_data_service.fetch_player_props(sport)
        
        # Convert to PlayerProp objects with confidence scores
        player_props = []
        for prop_data in props_data:
            try:
                prop_type = PropType(prop_data.get("prop_type", "").lower())
            except ValueError:
                # Skip unknown prop types
                continue
                
            confidence_score = self.prop_analyzer.calculate_confidence_score(
                prop_data["player_name"],
                prop_type,
                prop_data["line"]
            )
            
            hit_rate = self.prop_analyzer.get_player_hit_rate(
                prop_data["player_name"],
                prop_type
            )
            
            recent_performance = self.prop_analyzer.get_recent_performance(
                prop_data["player_name"],
                prop_type
            )
            
            # Get injury status
            injury_status = await self._get_player_injury_status(
                prop_data["player_name"], sport
            )
            
            player_prop = PlayerProp(
                player_name=prop_data["player_name"],
                team=prop_data["team"],
                opponent=prop_data["opponent"],
                prop_type=prop_type,
                line=prop_data["line"],
                over_odds=prop_data["over_odds"],
                under_odds=prop_data["under_odds"],
                confidence_score=confidence_score,
                hit_rate=hit_rate,
                recent_performance=recent_performance,
                injury_status=injury_status
            )
            
            player_props.append(player_prop)
        
        # Build parlays
        parlays = self.parlay_builder.build_parlays(player_props, sport, tier)
        self.stats["total_parlays_generated"] += len(parlays)
        
        return parlays
    
    async def _get_player_injury_status(self, player_name: str, sport: SportType) -> Optional[str]:
        """Get injury status for a player"""
        try:
            injury_data = await self.sports_data_service.fetch_injury_report(sport)
            for injury in injury_data:
                if injury.get("player_name") == player_name:
                    return injury.get("status", "Healthy")
            return "Healthy"
        except Exception as e:
            logger.warning(f"Could not fetch injury status for {player_name}: {str(e)}")
            return None
    
    async def get_system_stats(self) -> SystemStats:
        """Get system performance statistics"""
        # Calculate success rates by tier
        tier_stats = {}
        for tier in TierType:
            tier_parlays = []
            for parlays in self.parlay_cache.values():
                tier_parlays.extend([p for p in parlays if p.tier == tier])
            
            if tier_parlays:
                avg_confidence = sum(p.overall_confidence for p in tier_parlays) / len(tier_parlays)
                tier_stats[tier] = {
                    "count": len(tier_parlays),
                    "avg_confidence": avg_confidence
                }
            else:
                tier_stats[tier] = {"count": 0, "avg_confidence": 0}
        
        return SystemStats(
            total_parlays_generated=self.stats["total_parlays_generated"],
            success_rate_by_tier={
                tier: 0.85 if tier_stats[tier]["count"] > 0 else 0  # Mock success rate
                for tier in TierType
            },
            average_confidence_by_tier={
                tier: tier_stats[tier]["avg_confidence"]
                for tier in TierType
            },
            last_updated=datetime.now(),
            data_freshness={
                sport.value: self.last_refresh.get(sport.value, datetime.now())
                for sport in SportType
            }
        )
    
    async def cleanup(self):
        """Clean up resources"""
        await self.sports_data_service.close_session()
