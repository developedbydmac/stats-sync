#!/usr/bin/env python3
"""Debug confidence calculation components"""

import asyncio
from src.services.parlay_service import ParlayService
from src.models.parlay import SportType, PropType

async def debug_detailed_confidence():
    service = ParlayService()
    
    # Test specific high-performing players
    test_cases = [
        ("Travis Kelce", PropType.RECEIVING_YARDS, 65.5),
        ("Stefon Diggs", PropType.RECEIVING_YARDS, 85.5),
        ("Aaron Rodgers", PropType.PASSING_YARDS, 245.5),
        ("Davante Adams", PropType.RECEPTIONS, 7.5),
    ]
    
    for player_name, prop_type, line in test_cases:
        print(f"\n🔍 Debugging {player_name} - {prop_type.value}")
        print("=" * 50)
        
        # Get historical hit rate
        historical_hit_rate = service.prop_analyzer.get_player_hit_rate(player_name, prop_type, 90)
        print(f"Historical hit rate: {historical_hit_rate:.3f}")
        
        # Get recent form weight
        recent_form_weight = service.prop_analyzer.get_recent_form_weight(player_name, prop_type, 5)
        print(f"Recent form weight: {recent_form_weight:.3f}")
        
        # Get recent performance data
        recent_performance = service.prop_analyzer.get_recent_performance(player_name, prop_type, 5)
        print(f"Recent performance records: {len(recent_performance)}")
        if recent_performance:
            recent_hits = [game.get('hit', 0) for game in recent_performance]
            print(f"Recent hits: {recent_hits}")
        
        # Calculate final confidence
        base_confidence = historical_hit_rate * 100
        recent_adjustment = (recent_form_weight - 0.5) * 40
        final_confidence = base_confidence + recent_adjustment
        
        print(f"Base confidence: {base_confidence:.1f}%")
        print(f"Recent adjustment: {recent_adjustment:.1f}%")
        print(f"Final confidence: {final_confidence:.1f}%")

if __name__ == "__main__":
    asyncio.run(debug_detailed_confidence())
