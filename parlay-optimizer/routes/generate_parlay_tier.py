"""
Endpoint to generate preset tier parlays
Input: tier (e.g. "$100", "$500", "$1000", "$5000", "$10000")
Logic: Fetch recent player props using SportsDataIO
Select legs based on hit rate > 80% and estimated odds from historical trends
Combine legs until estimated payout matches target tier
Return: JSON with legs, estimated odds, confidence scores
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging

from models.parlay_schema import (
    TierParlayRequest, TierParlayResponse, ParlayTier, SportType, 
    ParlayResult, ParlayLeg, PlayerProp, RiskLevel
)
from services.sportsdata_io import SportsDataIOService
from utils.odds_math import (
    calculate_target_payout, calculate_required_odds, estimate_prop_odds,
    find_parlay_combination, calculate_parlay_odds, calculate_payout,
    calculate_confidence_score, calculate_parlay_probability
)

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate-tier-parlay", response_model=TierParlayResponse)
async def generate_tier_parlay(request: TierParlayRequest):
    """
    Generate a parlay for a specific payout tier
    
    Args:
        request: TierParlayRequest with tier and preferences
        
    Returns:
        TierParlayResponse with generated parlay and analysis
    """
    try:
        logger.info(f"Generating {request.tier} parlay for {request.sport}")
        
        # Initialize service
        sportsdata_service = SportsDataIOService()
        
        # Calculate target payout and required odds
        target_payout = calculate_target_payout(request.tier.value)
        required_odds = calculate_required_odds(target_payout, bet_amount=10.0)
        
        logger.info(f"Target payout: ${target_payout}, Required odds: {required_odds}")
        
        # Fetch high-hit-rate props
        recent_props = await sportsdata_service.get_recent_player_props(
            sport=request.sport,
            min_hit_rate=request.min_hit_rate
        )
        
        if not recent_props:
            raise HTTPException(status_code=404, detail="No suitable props found for this tier")
        
        # Estimate odds for each prop
        props_with_odds = []
        for prop_data in recent_props:
            estimated_odds = estimate_prop_odds(
                prop_data["prop_type"],
                line=0.5,  # Default line, would be calculated based on prop type
                hit_rate=prop_data["hit_rate"]
            )
            
            prop_data["estimated_odds"] = estimated_odds
            props_with_odds.append(prop_data)
        
        # Find best combination to reach target odds
        selected_props = find_parlay_combination(
            target_odds=required_odds,
            available_props=props_with_odds,
            max_legs=request.max_legs
        )
        
        if not selected_props:
            raise HTTPException(status_code=404, detail="Could not find suitable parlay combination")
        
        # Create parlay legs
        parlay_legs = []
        hit_rates = []
        
        for prop_data in selected_props:
            # Create PlayerProp object
            player_prop = PlayerProp(
                player_name=prop_data["player_name"],
                team=prop_data["team"],
                opponent="TBD",  # Would need opponent lookup
                prop_type=prop_data["prop_type"],
                line=_get_default_line(prop_data["prop_type"]),
                estimated_odds=prop_data["estimated_odds"],
                hit_rate=prop_data["hit_rate"],
                confidence_score=prop_data["confidence_score"],
                recent_form=prop_data.get("recent_form", []),
                game_date=prop_data["game_date"],
                position=prop_data.get("position", "")
            )
            
            # Create parlay leg
            leg = ParlayLeg(
                prop=player_prop,
                selection="over",  # Default to over
                odds=prop_data["estimated_odds"],
                confidence=prop_data["confidence_score"]
            )
            
            parlay_legs.append(leg)
            hit_rates.append(prop_data["hit_rate"])
        
        # Calculate combined odds and payout
        individual_odds = [leg.odds for leg in parlay_legs]
        total_odds = calculate_parlay_odds(individual_odds)
        estimated_payout = calculate_payout(total_odds, bet_amount=10.0)
        
        # Calculate confidence metrics
        confidence_score = calculate_confidence_score(hit_rates)
        hit_probability = calculate_parlay_probability(hit_rates)
        
        # Determine risk level based on confidence
        if confidence_score >= 80:
            risk_level = RiskLevel.LOW
        elif confidence_score >= 60:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH
        
        # Create parlay result
        parlay_result = ParlayResult(
            legs=parlay_legs,
            total_odds=total_odds,
            estimated_payout=estimated_payout,
            confidence_score=confidence_score,
            hit_probability=hit_probability,
            risk_level=risk_level
        )
        
        # Analysis data
        analysis = {
            "target_payout": target_payout,
            "actual_payout": estimated_payout,
            "payout_difference": estimated_payout - target_payout,
            "payout_accuracy": min(estimated_payout, target_payout) / max(estimated_payout, target_payout),
            "average_hit_rate": sum(hit_rates) / len(hit_rates),
            "legs_count": len(parlay_legs),
            "risk_assessment": {
                "level": risk_level.value,
                "factors": {
                    "hit_rate_variance": max(hit_rates) - min(hit_rates),
                    "leg_count_impact": (len(parlay_legs) - 2) * 0.1,
                    "confidence_distribution": confidence_score
                }
            }
        }
        
        # Clean up
        await sportsdata_service.close_session()
        
        response = TierParlayResponse(
            tier=request.tier,
            target_payout=target_payout,
            parlay=parlay_result,
            analysis=analysis
        )
        
        logger.info(f"Generated {request.tier} parlay with {len(parlay_legs)} legs, "
                   f"confidence: {confidence_score:.1f}%, payout: ${estimated_payout:.2f}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating tier parlay: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating parlay: {str(e)}")

def _get_default_line(prop_type: str) -> float:
    """Get default line value for prop type"""
    line_defaults = {
        "hits": 0.5,
        "home_runs": 0.5,
        "rbis": 0.5,
        "strikeouts": 0.5,
        "passing_yards": 249.5,
        "rushing_yards": 49.5,
        "receiving_yards": 49.5,
        "receptions": 3.5,
        "points": 19.5,
        "assists": 4.5,
        "rebounds": 7.5
    }
    return line_defaults.get(prop_type, 0.5)
