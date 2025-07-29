#!/usr/bin/env python3
"""Debug script to check confidence scores"""

import asyncio
from src.services.parlay_service import ParlayService
from src.models.parlay import SportType, TierType, PropType

async def debug_confidence():
    service = ParlayService()
    
    # Get fresh props data
    props_data = await service.sports_data_service.fetch_player_props(SportType.NFL)
    
    print("Confidence scores for NFL props:")
    print("=" * 60)
    
    for prop_data in props_data:
        try:
            prop_type = PropType(prop_data.get("prop_type", "").lower())
        except ValueError:
            continue
            
        confidence_score = service.prop_analyzer.calculate_confidence_score(
            prop_data["player_name"],
            prop_type,
            prop_data["line"]
        )
        
        player_name = prop_data["player_name"]
        prop_type_str = prop_data["prop_type"]
        line = prop_data["line"]
        
        print(f"{player_name:<20} {prop_type_str:<15} Line: {line:<6} Confidence: {confidence_score:.1f}%")
        
        # Check if this would qualify for different tiers
        tiers = []
        if confidence_score >= 70: tiers.append("FREE")
        if confidence_score >= 80: tiers.append("PREMIUM") 
        if confidence_score >= 95: tiers.append("GOAT")
        
        if tiers:
            print(f"{'':>20} Qualifies for: {', '.join(tiers)}")
        print()

if __name__ == "__main__":
    asyncio.run(debug_confidence())
