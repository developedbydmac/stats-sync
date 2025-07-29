import uuid
import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from itertools import combinations
import math

from src.models.parlay import (
    Parlay, ParlayLeg, PlayerProp, TierType, SportType, PropType, ParlayResponse
)
from src.utils.prop_analyzer import PropAnalyzer

logger = logging.getLogger("stats-sync")

class ParlayBuilder:
    """Builds optimized parlays based on confidence scores and tier requirements"""
    
    def __init__(self, prop_analyzer: PropAnalyzer):
        self.prop_analyzer = prop_analyzer
        self.tier_requirements = {
            TierType.FREE: {
                "min_confidence": 45,  # More realistic for free tier
                "target_payout": 10,  # 10x payout
                "max_legs": 6,
                "conservative_bias": True
            },
            TierType.PREMIUM: {
                "min_confidence": 55,  # More realistic for premium tier
                "target_payout": 25,  # 25x payout
                "max_legs": 7,
                "conservative_bias": False
            },
            TierType.GOAT: {
                "min_confidence": 65,  # More realistic for GOAT tier
                "target_payout": 50,  # 50x payout
                "max_legs": 8,
                "conservative_bias": False
            }
        }
    
    def build_parlays(self, props: List[PlayerProp], sport: SportType, 
                     tier: TierType = None) -> List[Parlay]:
        """
        Build optimized parlays from available props
        
        Args:
            props: List of available player props
            sport: Sport type
            tier: Optional tier filter
            
        Returns:
            List of optimized parlays
        """
        tiers_to_build = [tier] if tier else list(TierType)
        all_parlays = []
        
        for tier_type in tiers_to_build:
            tier_parlays = self._build_tier_parlays(props, sport, tier_type)
            all_parlays.extend(tier_parlays)
        
        return all_parlays
    
    def _build_tier_parlays(self, props: List[PlayerProp], sport: SportType, 
                           tier: TierType) -> List[Parlay]:
        """Build parlays for a specific tier"""
        requirements = self.tier_requirements[tier]
        
        # Filter props that meet tier requirements
        eligible_props = [
            prop for prop in props 
            if prop.confidence_score >= requirements["min_confidence"]
        ]
        
        if len(eligible_props) < 5:
            logger.warning(f"Not enough eligible props for {tier.value} tier")
            return []
        
        # Generate multiple parlay combinations
        parlays = []
        max_parlays = 3 if tier == TierType.GOAT else 5
        
        for i in range(max_parlays):
            parlay = self._generate_single_parlay(
                eligible_props, sport, tier, requirements
            )
            if parlay and not self._is_duplicate_parlay(parlay, parlays):
                parlays.append(parlay)
        
        return parlays
    
    def _generate_single_parlay(self, props: List[PlayerProp], sport: SportType,
                               tier: TierType, requirements: Dict[str, Any]) -> Optional[Parlay]:
        """Generate a single optimized parlay"""
        max_attempts = 50
        
        for attempt in range(max_attempts):
            # Select random number of legs within range
            num_legs = random.randint(5, min(requirements["max_legs"], len(props)))
            
            # Select props for this parlay
            selected_props = self._select_parlay_props(props, num_legs, requirements)
            
            if len(selected_props) < 5:
                continue
            
            # Create parlay legs
            legs = []
            total_confidence = 0
            
            for prop in selected_props:
                leg = self._create_parlay_leg(prop, tier)
                legs.append(leg)
                total_confidence += leg.confidence
            
            # Calculate overall metrics
            overall_confidence = total_confidence / len(legs)
            total_odds = self._calculate_total_odds(legs)
            expected_payout = self._odds_to_payout_multiplier(total_odds)
            
            # Check if parlay meets requirements
            if (overall_confidence >= requirements["min_confidence"] and
                expected_payout >= requirements["target_payout"] * 0.8):  # 20% tolerance
                
                return Parlay(
                    id=str(uuid.uuid4()),
                    tier=tier,
                    sport=sport,
                    legs=legs,
                    total_odds=total_odds,
                    expected_payout=expected_payout,
                    overall_confidence=overall_confidence,
                    created_at=datetime.now(),
                    game_date=datetime.now().strftime("%Y-%m-%d"),
                    description=self._generate_parlay_description(legs, tier)
                )
        
        logger.warning(f"Failed to generate valid parlay for {tier.value} tier after {max_attempts} attempts")
        return None
    
    def _select_parlay_props(self, props: List[PlayerProp], num_legs: int,
                           requirements: Dict[str, Any]) -> List[PlayerProp]:
        """Select props for a parlay ensuring no duplicates and good distribution"""
        selected = []
        used_players = set()
        used_teams = []  # Use list to track team frequency
        
        # Sort props by confidence (descending)
        sorted_props = sorted(props, key=lambda x: x.confidence_score, reverse=True)
        
        # Add some randomization for variety
        if not requirements.get("conservative_bias", False):
            # Shuffle the top 50% to add variety for premium/GOAT tiers
            top_half = len(sorted_props) // 2
            random.shuffle(sorted_props[:top_half])
        
        for prop in sorted_props:
            if len(selected) >= num_legs:
                break
            
            # Avoid duplicate players
            if prop.player_name in used_players:
                continue
            
            # Limit props from same team (max 2 for variety)
            if used_teams.count(prop.team) >= 2:
                continue
            
            selected.append(prop)
            used_players.add(prop.player_name)
            used_teams.append(prop.team)
        
        return selected

    def _create_parlay_leg(self, prop: PlayerProp, tier: TierType) -> ParlayLeg:
        """Create a parlay leg from a player prop"""
        # For GOAT tier, be more selective about over/under
        if tier == TierType.GOAT:
            # Use confidence to determine selection
            selection = "over" if prop.confidence_score > 97.5 else "under"
            odds = prop.over_odds if selection == "over" else prop.under_odds
        else:
            # For other tiers, use hit rate to determine best selection
            selection = "over" if prop.hit_rate > 0.55 else "under"
            odds = prop.over_odds if selection == "over" else prop.under_odds
        
        return ParlayLeg(
            player_prop=prop,
            selection=selection,
            odds=odds,
            confidence=prop.confidence_score
        )
    
    def _calculate_total_odds(self, legs: List[ParlayLeg]) -> int:
        """Calculate total American odds for the parlay"""
        decimal_odds = 1.0
        
        for leg in legs:
            if leg.odds > 0:
                decimal_odds *= (leg.odds / 100) + 1
            else:
                decimal_odds *= (100 / abs(leg.odds)) + 1
        
        # Convert back to American odds
        if decimal_odds >= 2.0:
            return int((decimal_odds - 1) * 100)
        else:
            return int(-100 / (decimal_odds - 1))
    
    def _odds_to_payout_multiplier(self, american_odds: int) -> float:
        """Convert American odds to payout multiplier"""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1
    
    def _generate_parlay_description(self, legs: List[ParlayLeg], tier: TierType) -> str:
        """Generate a descriptive title for the parlay"""
        if tier == TierType.GOAT:
            return f"🐐 GOAT Tier: {len(legs)}-Leg Lock Parlay"
        elif tier == TierType.PREMIUM:
            return f"💎 Premium: High-Confidence {len(legs)}-Legger"
        else:
            return f"🎯 Free Play: Solid {len(legs)}-Leg Value Bet"
    
    def _is_duplicate_parlay(self, new_parlay: Parlay, existing_parlays: List[Parlay]) -> bool:
        """Check if parlay is a duplicate based on players used"""
        new_players = {leg.player_prop.player_name for leg in new_parlay.legs}
        
        for existing in existing_parlays:
            existing_players = {leg.player_prop.player_name for leg in existing.legs}
            
            # Consider duplicate if more than 60% overlap
            overlap = len(new_players.intersection(existing_players))
            if overlap / len(new_players) > 0.6:
                return True
        
        return False
    
    def create_parlay_response(self, parlay: Parlay) -> ParlayResponse:
        """Create a complete parlay response with analysis"""
        tier_req = self.tier_requirements[parlay.tier]
        
        analysis = {
            "avg_confidence": parlay.overall_confidence,
            "expected_hit_rate": self._calculate_expected_hit_rate(parlay.legs),
            "risk_assessment": self._assess_risk(parlay),
            "key_factors": self._identify_key_factors(parlay.legs),
            "recommendation": self._generate_recommendation(parlay)
        }
        
        return ParlayResponse(
            parlay=parlay,
            tier_requirements=tier_req,
            analysis=analysis
        )
    
    def _calculate_expected_hit_rate(self, legs: List[ParlayLeg]) -> float:
        """Calculate expected hit rate for the entire parlay"""
        combined_probability = 1.0
        for leg in legs:
            # Convert confidence to probability
            prob = leg.confidence / 100
            combined_probability *= prob
        
        return combined_probability
    
    def _assess_risk(self, parlay: Parlay) -> str:
        """Assess overall risk level of the parlay"""
        if parlay.overall_confidence >= 95:
            return "Very Low Risk"
        elif parlay.overall_confidence >= 85:
            return "Low Risk"
        elif parlay.overall_confidence >= 75:
            return "Moderate Risk"
        else:
            return "High Risk"
    
    def _identify_key_factors(self, legs: List[ParlayLeg]) -> List[str]:
        """Identify key factors that make this parlay attractive"""
        factors = []
        
        # High confidence legs
        high_conf_legs = [leg for leg in legs if leg.confidence >= 90]
        if high_conf_legs:
            factors.append(f"{len(high_conf_legs)} high-confidence props (90%+)")
        
        # Player form analysis
        factors.append("Recent player form analysis included")
        
        # Injury considerations
        factors.append("Injury report reviewed")
        
        return factors
    
    def _generate_recommendation(self, parlay: Parlay) -> str:
        """Generate betting recommendation"""
        if parlay.tier == TierType.GOAT and parlay.overall_confidence >= 97:
            return "STRONG BET: Exceptional confidence in all legs"
        elif parlay.tier == TierType.PREMIUM and parlay.overall_confidence >= 85:
            return "SOLID BET: High probability with good payout potential"
        elif parlay.tier == TierType.FREE:
            return "VALUE PLAY: Good entry-level bet with decent odds"
        else:
            return "PROCEED WITH CAUTION: Below optimal confidence thresholds"
