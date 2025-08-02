"""
Odds calculation and parlay math utilities
"""
from typing import List, Tuple
import math

def american_to_decimal(american_odds: int) -> float:
    """Convert American odds to decimal odds"""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1

def decimal_to_american(decimal_odds: float) -> int:
    """Convert decimal odds to American odds"""
    if decimal_odds >= 2.0:
        return int((decimal_odds - 1) * 100)
    else:
        return int(-100 / (decimal_odds - 1))

def calculate_parlay_odds(individual_odds: List[int]) -> int:
    """Calculate combined parlay odds from individual American odds"""
    decimal_odds = [american_to_decimal(odds) for odds in individual_odds]
    combined_decimal = 1.0
    for odds in decimal_odds:
        combined_decimal *= odds
    return decimal_to_american(combined_decimal)

def calculate_payout(odds: int, bet_amount: float = 10.0) -> float:
    """Calculate payout for given odds and bet amount"""
    decimal_odds = american_to_decimal(odds)
    return bet_amount * decimal_odds

def calculate_hit_probability(odds: int) -> float:
    """Calculate implied probability from American odds"""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

def calculate_parlay_probability(individual_probabilities: List[float]) -> float:
    """Calculate combined probability of parlay hitting"""
    combined_prob = 1.0
    for prob in individual_probabilities:
        combined_prob *= prob
    return combined_prob

def estimate_prop_odds(prop_type: str, line: float, hit_rate: float) -> int:
    """
    Estimate odds for a player prop based on type, line, and historical hit rate
    
    Args:
        prop_type: Type of prop (hits, home_runs, etc.)
        line: The line value (e.g. 0.5 for home runs)
        hit_rate: Historical hit rate (0-1)
        
    Returns:
        Estimated American odds
    """
    # Base odds estimations for common props
    base_odds_map = {
        "hits": {
            0.5: +180,  # Over 0.5 hits
            1.5: +240,  # Over 1.5 hits
            2.5: +400   # Over 2.5 hits
        },
        "home_runs": {
            0.5: +240,  # Over 0.5 HRs
            1.5: +800   # Over 1.5 HRs
        },
        "rbis": {
            0.5: +160,  # Over 0.5 RBIs
            1.5: +300,  # Over 1.5 RBIs
            2.5: +500   # Over 2.5 RBIs
        },
        "strikeouts": {
            0.5: +140,  # Over 0.5 Ks (batter)
            5.5: +180,  # Over 5.5 Ks (pitcher)
            7.5: +300   # Over 7.5 Ks (pitcher)
        },
        "passing_yards": {
            249.5: +110,  # Over 249.5 passing yards
            299.5: +160,  # Over 299.5 passing yards
            349.5: +250   # Over 349.5 passing yards
        },
        "rushing_yards": {
            49.5: +120,   # Over 49.5 rushing yards
            79.5: +200,   # Over 79.5 rushing yards
            99.5: +300    # Over 99.5 rushing yards
        },
        "receiving_yards": {
            49.5: +110,   # Over 49.5 receiving yards
            69.5: +160,   # Over 69.5 receiving yards
            89.5: +250    # Over 89.5 receiving yards
        },
        "receptions": {
            3.5: +120,    # Over 3.5 receptions
            5.5: +180,    # Over 5.5 receptions
            7.5: +300     # Over 7.5 receptions
        }
    }
    
    # Get base odds for this prop type and line
    base_odds = +200  # Default if not found
    if prop_type in base_odds_map:
        prop_lines = base_odds_map[prop_type]
        if line in prop_lines:
            base_odds = prop_lines[line]
        else:
            # Find closest line
            closest_line = min(prop_lines.keys(), key=lambda x: abs(x - line))
            base_odds = prop_lines[closest_line]
            
            # Adjust for line difference
            line_diff = line - closest_line
            if line_diff > 0:
                base_odds += int(line_diff * 50)  # Higher line = higher odds
            else:
                base_odds -= int(abs(line_diff) * 30)  # Lower line = lower odds
    
    # Adjust based on hit rate
    if hit_rate > 0.8:
        # High hit rate = lower odds
        adjustment = int((hit_rate - 0.8) * 500)
        base_odds -= adjustment
    elif hit_rate < 0.6:
        # Low hit rate = higher odds
        adjustment = int((0.6 - hit_rate) * 800)
        base_odds += adjustment
    
    # Ensure odds are reasonable
    base_odds = max(-500, min(base_odds, +2000))
    
    return base_odds

def find_parlay_combination(target_odds: int, available_props: List[dict], max_legs: int = 8) -> List[dict]:
    """
    Find combination of props that gets close to target odds
    
    Args:
        target_odds: Target American odds (e.g. +2640)
        available_props: List of available props with estimated odds
        max_legs: Maximum number of legs
        
    Returns:
        List of selected props for parlay
    """
    target_decimal = american_to_decimal(target_odds)
    best_combination = []
    best_diff = float('inf')
    
    # Sort props by confidence (highest first)
    sorted_props = sorted(available_props, key=lambda x: x.get('confidence_score', 0), reverse=True)
    
    # Try different combinations
    from itertools import combinations
    
    for num_legs in range(2, min(max_legs + 1, len(sorted_props) + 1)):
        for combo in combinations(sorted_props[:min(20, len(sorted_props))], num_legs):
            combo_odds = [prop.get('estimated_odds', +200) for prop in combo]
            combined_decimal = 1.0
            for odds in combo_odds:
                combined_decimal *= american_to_decimal(odds)
            
            diff = abs(combined_decimal - target_decimal)
            if diff < best_diff:
                best_diff = diff
                best_combination = list(combo)
                
                # If we're close enough, stop searching
                if diff < target_decimal * 0.1:  # Within 10%
                    break
        
        if best_diff < target_decimal * 0.1:
            break
    
    return best_combination

def calculate_target_payout(tier: str) -> float:
    """Calculate target payout for tier"""
    tier_payouts = {
        "$100": 100.0,
        "$500": 500.0,
        "$1000": 1000.0,
        "$5000": 5000.0,
        "$10000": 10000.0
    }
    return tier_payouts.get(tier, 100.0)

def calculate_required_odds(target_payout: float, bet_amount: float = 10.0) -> int:
    """Calculate required odds to reach target payout"""
    required_decimal = target_payout / bet_amount
    return decimal_to_american(required_decimal)

def calculate_confidence_score(hit_rates: List[float], recent_form_weights: List[float] = None) -> float:
    """
    Calculate overall confidence score for parlay
    
    Args:
        hit_rates: List of individual prop hit rates
        recent_form_weights: Optional weights for recent form
        
    Returns:
        Confidence score (0-100)
    """
    if not hit_rates:
        return 0.0
    
    # Base confidence from hit rates
    avg_hit_rate = sum(hit_rates) / len(hit_rates)
    base_confidence = avg_hit_rate * 100
    
    # Adjust for number of legs (more legs = lower confidence)
    leg_penalty = (len(hit_rates) - 2) * 5  # 5% penalty per leg over 2
    adjusted_confidence = base_confidence - leg_penalty
    
    # Apply recent form weights if provided
    if recent_form_weights and len(recent_form_weights) == len(hit_rates):
        weighted_avg = sum(rate * weight for rate, weight in zip(hit_rates, recent_form_weights))
        weighted_avg /= sum(recent_form_weights)
        adjusted_confidence = (adjusted_confidence + weighted_avg * 100) / 2
    
    return max(0.0, min(100.0, adjusted_confidence))
