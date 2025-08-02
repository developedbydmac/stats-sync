"""
Endpoint to build parlay based on user input odds (e.g. +2640)
Input: target_odds, risk_level (low, med, high)
Use SportsDataIO to fetch high-hit-rate props (last 10 games)
Estimate each leg's odds using typical ranges (e.g. Over 0.5 HRs ≈ +240)
Build combo of legs to exceed target odds
Return: parlay JSON with estimated payout and total odds
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging

from models.parlay_schema import (
    CustomParlayRequest, CustomParlayResponse, SportType, 
    ParlayResult, ParlayLeg, PlayerProp, RiskLevel
)
from services.sportsdata_io import SportsDataIOService
from utils.odds_math import (
    estimate_prop_odds, find_parlay_combination, calculate_parlay_odds, 
    calculate_payout, calculate_confidence_score, calculate_parlay_probability,
    american_to_decimal, calculate_hit_probability
)

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate-custom-parlay", response_model=CustomParlayResponse)
async def generate_custom_parlay(request: CustomParlayRequest):
    """
    Generate a parlay targeting specific odds
    
    Args:
        request: CustomParlayRequest with target odds and preferences
        
    Returns:
        CustomParlayResponse with generated parlay and odds analysis
    """
    try:
        logger.info(f"Generating custom parlay with target odds {request.target_odds} "
                   f"for {request.sport}, risk level: {request.risk_level}")
        
        # Initialize service
        sportsdata_service = SportsDataIOService()
        
        # Adjust min hit rate based on risk level
        min_hit_rate = _get_min_hit_rate_for_risk(request.risk_level, request.min_hit_rate)
        
        # Fetch suitable props based on risk level
        recent_props = await sportsdata_service.get_recent_player_props(
            sport=request.sport,
            min_hit_rate=min_hit_rate
        )
        
        if not recent_props:
            raise HTTPException(
                status_code=404, 
                detail=f"No suitable props found for {request.risk_level} risk level"
            )
        
        # Filter props based on risk level preferences
        filtered_props = _filter_props_by_risk_level(recent_props, request.risk_level)
        
        # Estimate odds for each prop
        props_with_odds = []
        for prop_data in filtered_props:
            estimated_odds = estimate_prop_odds(
                prop_data["prop_type"],
                line=_get_default_line(prop_data["prop_type"]),
                hit_rate=prop_data["hit_rate"]
            )
            
            # Adjust odds based on risk level preference
            adjusted_odds = _adjust_odds_for_risk_level(estimated_odds, request.risk_level)
            
            prop_data["estimated_odds"] = adjusted_odds
            props_with_odds.append(prop_data)
        
        # Find best combination to reach target odds
        selected_props = find_parlay_combination(
            target_odds=request.target_odds,
            available_props=props_with_odds,
            max_legs=request.max_legs
        )
        
        if not selected_props:
            raise HTTPException(
                status_code=404, 
                detail=f"Could not find suitable combination for target odds {request.target_odds}"
            )
        
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
            
            # Create parlay leg (adjust selection based on odds)
            selection = "over" if prop_data["estimated_odds"] > 0 else "under"
            
            leg = ParlayLeg(
                prop=player_prop,
                selection=selection,
                odds=prop_data["estimated_odds"],
                confidence=prop_data["confidence_score"]
            )
            
            parlay_legs.append(leg)
            hit_rates.append(prop_data["hit_rate"])
        
        # Calculate actual combined odds and payout
        individual_odds = [leg.odds for leg in parlay_legs]
        actual_odds = calculate_parlay_odds(individual_odds)
        estimated_payout = calculate_payout(actual_odds, bet_amount=10.0)
        
        # Calculate confidence metrics
        confidence_score = calculate_confidence_score(hit_rates)
        hit_probability = calculate_parlay_probability(hit_rates)
        
        # Create parlay result
        parlay_result = ParlayResult(
            legs=parlay_legs,
            total_odds=actual_odds,
            estimated_payout=estimated_payout,
            confidence_score=confidence_score,
            hit_probability=hit_probability,
            risk_level=request.risk_level
        )
        
        # Odds analysis
        target_probability = calculate_hit_probability(request.target_odds)
        actual_probability = calculate_hit_probability(actual_odds)
        
        odds_analysis = {
            "target_odds": request.target_odds,
            "actual_odds": actual_odds,
            "odds_difference": actual_odds - request.target_odds,
            "odds_accuracy": min(abs(actual_odds), abs(request.target_odds)) / max(abs(actual_odds), abs(request.target_odds)),
            "target_probability": target_probability,
            "actual_probability": actual_probability,
            "probability_difference": abs(actual_probability - target_probability),
            "risk_assessment": {
                "requested_level": request.risk_level.value,
                "calculated_level": _calculate_actual_risk_level(confidence_score),
                "risk_factors": {
                    "leg_count": len(parlay_legs),
                    "average_hit_rate": sum(hit_rates) / len(hit_rates),
                    "hit_rate_variance": max(hit_rates) - min(hit_rates),
                    "odds_variance": max(individual_odds) - min(individual_odds)
                }
            },
            "recommendation": _generate_recommendation(
                request.target_odds, actual_odds, confidence_score, request.risk_level
            )
        }
        
        # Clean up
        await sportsdata_service.close_session()
        
        response = CustomParlayResponse(
            target_odds=request.target_odds,
            actual_odds=actual_odds,
            parlay=parlay_result,
            odds_analysis=odds_analysis
        )
        
        logger.info(f"Generated custom parlay: target {request.target_odds} vs actual {actual_odds}, "
                   f"confidence: {confidence_score:.1f}%, {len(parlay_legs)} legs")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating custom parlay: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating custom parlay: {str(e)}")

def _get_min_hit_rate_for_risk(risk_level: RiskLevel, base_min_hit_rate: float) -> float:
    """Adjust minimum hit rate based on risk level"""
    risk_adjustments = {
        RiskLevel.LOW: 0.1,      # Increase min hit rate for low risk
        RiskLevel.MEDIUM: 0.0,   # Use base hit rate
        RiskLevel.HIGH: -0.1     # Decrease min hit rate for high risk
    }
    
    adjustment = risk_adjustments.get(risk_level, 0.0)
    return max(0.5, min(0.95, base_min_hit_rate + adjustment))

def _filter_props_by_risk_level(props: List[dict], risk_level: RiskLevel) -> List[dict]:
    """Filter props based on risk level preferences"""
    if risk_level == RiskLevel.LOW:
        # Prefer props with very high hit rates and consistency
        return [p for p in props if p["hit_rate"] >= 0.85 and p["confidence_score"] >= 85]
    elif risk_level == RiskLevel.MEDIUM:
        # Balanced approach
        return [p for p in props if p["hit_rate"] >= 0.75 and p["confidence_score"] >= 75]
    else:  # HIGH risk
        # Accept lower hit rates for potentially higher payouts
        return [p for p in props if p["hit_rate"] >= 0.6 and p["confidence_score"] >= 60]

def _adjust_odds_for_risk_level(odds: int, risk_level: RiskLevel) -> int:
    """Adjust estimated odds based on risk level preference"""
    if risk_level == RiskLevel.LOW:
        # Conservative odds (slightly worse)
        return int(odds * 0.9) if odds > 0 else int(odds * 1.1)
    elif risk_level == RiskLevel.HIGH:
        # Aggressive odds (slightly better)
        return int(odds * 1.1) if odds > 0 else int(odds * 0.9)
    else:
        # Medium risk - use estimated odds as-is
        return odds

def _calculate_actual_risk_level(confidence_score: float) -> str:
    """Calculate actual risk level based on confidence score"""
    if confidence_score >= 80:
        return "low"
    elif confidence_score >= 60:
        return "medium"
    else:
        return "high"

def _generate_recommendation(target_odds: int, actual_odds: int, confidence: float, risk_level: RiskLevel) -> str:
    """Generate recommendation based on parlay analysis"""
    odds_diff_pct = abs(actual_odds - target_odds) / abs(target_odds) * 100
    
    recommendations = []
    
    # Odds accuracy
    if odds_diff_pct <= 10:
        recommendations.append("Excellent odds match")
    elif odds_diff_pct <= 25:
        recommendations.append("Good odds approximation")
    else:
        recommendations.append("Consider adjusting target odds")
    
    # Confidence assessment
    if confidence >= 80:
        recommendations.append("High confidence parlay")
    elif confidence >= 60:
        recommendations.append("Moderate confidence - consider smaller bet")
    else:
        recommendations.append("Low confidence - high risk")
    
    # Risk level alignment
    calculated_risk = _calculate_actual_risk_level(confidence)
    if calculated_risk == risk_level.value:
        recommendations.append("Risk level matches expectations")
    else:
        recommendations.append(f"Actual risk is {calculated_risk}, requested {risk_level.value}")
    
    return " | ".join(recommendations)

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
