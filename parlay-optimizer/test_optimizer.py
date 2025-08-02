#!/usr/bin/env python3
"""
Test the Parlay Optimizer API
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8002"

def test_api_health():
    """Test API health check"""
    print("🏥 Testing API Health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Status: {data['status']}")
            print(f"   API Key Configured: {data['api_key_configured']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    return True

def test_tier_parlay():
    """Test tier-based parlay generation"""
    print("\n💰 Testing Tier Parlay Generation...")
    
    request_data = {
        "tier": "$500",
        "sport": "mlb",
        "max_legs": 6,
        "min_hit_rate": 0.8
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/generate-tier-parlay",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generated {data['tier']} parlay")
            print(f"   Target Payout: ${data['target_payout']}")
            print(f"   Actual Payout: ${data['parlay']['estimated_payout']:.2f}")
            print(f"   Total Odds: {data['parlay']['total_odds']}")
            print(f"   Confidence: {data['parlay']['confidence_score']:.1f}%")
            print(f"   Legs: {len(data['parlay']['legs'])}")
            
            # Show each leg
            for i, leg in enumerate(data['parlay']['legs'], 1):
                prop = leg['prop']
                print(f"     Leg {i}: {prop['player_name']} {prop['prop_type']} {leg['selection']} {prop['line']} ({leg['odds']})")
            
        else:
            print(f"❌ Failed to generate tier parlay: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing tier parlay: {e}")

def test_custom_parlay():
    """Test custom odds parlay generation"""
    print("\n🎯 Testing Custom Parlay Generation...")
    
    request_data = {
        "target_odds": 2640,  # +2640 odds
        "risk_level": "med",
        "sport": "mlb",
        "max_legs": 8,
        "min_hit_rate": 0.7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/generate-custom-parlay",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generated custom parlay")
            print(f"   Target Odds: +{data['target_odds']}")
            print(f"   Actual Odds: {data['actual_odds']}")
            print(f"   Estimated Payout: ${data['parlay']['estimated_payout']:.2f}")
            print(f"   Confidence: {data['parlay']['confidence_score']:.1f}%")
            print(f"   Hit Probability: {data['parlay']['hit_probability']:.3f}")
            print(f"   Risk Level: {data['parlay']['risk_level']}")
            print(f"   Legs: {len(data['parlay']['legs'])}")
            
            # Show recommendation
            recommendation = data['odds_analysis']['recommendation']
            print(f"   Recommendation: {recommendation}")
            
            # Show each leg
            for i, leg in enumerate(data['parlay']['legs'], 1):
                prop = leg['prop']
                print(f"     Leg {i}: {prop['player_name']} {prop['prop_type']} {leg['selection']} {prop['line']} ({leg['odds']})")
            
        else:
            print(f"❌ Failed to generate custom parlay: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing custom parlay: {e}")

def test_info_endpoints():
    """Test informational endpoints"""
    print("\n📊 Testing Info Endpoints...")
    
    endpoints = [
        ("/api/v1/tiers", "Available Tiers"),
        ("/api/v1/sports", "Supported Sports"),
        ("/api/v1/risk-levels", "Risk Levels")
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: Retrieved successfully")
                
                if "tiers" in data:
                    print(f"   Available tiers: {[t['tier'] for t in data['tiers']]}")
                elif "sports" in data:
                    print(f"   Supported sports: {list(data['sports'].keys())}")
                elif "risk_levels" in data:
                    print(f"   Risk levels: {list(data['risk_levels'].keys())}")
                    
            else:
                print(f"❌ {name}: Failed ({response.status_code})")
                
        except Exception as e:
            print(f"❌ Error testing {name}: {e}")

def main():
    """Run all tests"""
    print("🏆 Parlay Optimizer API Test Suite")
    print("=" * 50)
    
    # Test API health first
    if not test_api_health():
        print("\n❌ API is not responding. Make sure the server is running:")
        print("   cd parlay-optimizer")
        print("   python main.py")
        sys.exit(1)
    
    # Test endpoints
    test_info_endpoints()
    test_tier_parlay()
    test_custom_parlay()
    
    print("\n🎉 Test suite completed!")
    print("\nAPI Documentation available at: http://localhost:8002/docs")
    print("\nExample requests:")
    print("  Tier Parlay: POST /api/v1/generate-tier-parlay")
    print("  Custom Parlay: POST /api/v1/generate-custom-parlay")

if __name__ == "__main__":
    main()
