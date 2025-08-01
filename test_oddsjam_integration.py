#!/usr/bin/env python3
"""
Test OddsJam integration
"""
import asyncio
import os
import sys
sys.path.append('.')

from src.services.oddsjam_service import OddsJamService
from src.models.parlay import SportType

async def test_oddsjam_integration():
    """Test OddsJam service integration"""
    
    print("Testing OddsJam API Integration")
    print("=" * 50)
    
    oddsjam_service = OddsJamService()
    
    # Test 1: Check API key configuration
    print(f"API Key configured: {'Yes' if oddsjam_service.api_key and oddsjam_service.api_key != 'your_oddsjam_key_here' else 'No'}")
    
    if not oddsjam_service.api_key or oddsjam_service.api_key == "your_oddsjam_key_here":
        print("⚠️  OddsJam API key not configured - service will return empty results")
        print("   To test with real data, add your OddsJam API key to .env file")
    
    # Test 2: Fetch available sports
    print("\n📊 Testing available sports...")
    try:
        sports = await oddsjam_service.get_available_sports()
        print(f"Available sports: {sports}")
    except Exception as e:
        print(f"Error fetching sports: {e}")
    
    # Test 3: Fetch player props for MLB
    print("\n⚾ Testing MLB player props...")
    try:
        mlb_props = await oddsjam_service.fetch_player_props(SportType.MLB)
        print(f"MLB props fetched: {len(mlb_props)}")
        
        if mlb_props:
            sample_prop = mlb_props[0]
            print(f"Sample prop: {sample_prop.player_name} - {sample_prop.prop_type.value} {sample_prop.line}")
            print(f"Odds: Over {sample_prop.over_odds}, Under {sample_prop.under_odds}")
    except Exception as e:
        print(f"Error fetching MLB props: {e}")
    
    # Test 4: Fetch player props for NFL
    print("\n🏈 Testing NFL player props...")
    try:
        nfl_props = await oddsjam_service.fetch_player_props(SportType.NFL)
        print(f"NFL props fetched: {len(nfl_props)}")
        
        if nfl_props:
            sample_prop = nfl_props[0]
            print(f"Sample prop: {sample_prop.player_name} - {sample_prop.prop_type.value} {sample_prop.line}")
            print(f"Odds: Over {sample_prop.over_odds}, Under {sample_prop.under_odds}")
    except Exception as e:
        print(f"Error fetching NFL props: {e}")
    
    # Test 5: Fetch live props
    print("\n🔴 Testing live props...")
    try:
        live_props = await oddsjam_service.fetch_live_props(SportType.MLB)
        print(f"Live props fetched: {len(live_props)}")
        
        if live_props:
            sample_live = live_props[0]
            print(f"Sample live prop: {sample_live.player_name} - {sample_live.prop_type.value}")
    except Exception as e:
        print(f"Error fetching live props: {e}")
    
    # Cleanup
    await oddsjam_service.close_session()
    
    print("\n✅ OddsJam integration test completed!")
    print("\nNext steps:")
    print("1. Add your OddsJam API key to .env file for real data")
    print("2. Start the server: python main.py")
    print("3. Test endpoints:")
    print("   - http://localhost:8001/props/mlb (now includes OddsJam data)")
    print("   - http://localhost:8001/parlays/live?sport=mlb (live parlays)")

if __name__ == "__main__":
    asyncio.run(test_oddsjam_integration())
