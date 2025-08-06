#!/usr/bin/env python3
"""
Example script demonstrating how to use the Stats Sync API
"""
import requests
import json
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"
SPORT = "NFL"
DATE = datetime.now().strftime("%Y-%m-%d")
TIER = "Premium"

def test_api_endpoints():
    """Test all the main API endpoints"""
    print("🧪 Testing Stats Sync API Endpoints")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1️⃣ Testing Health Check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Prediction Status
    print("\n2️⃣ Testing Prediction Status...")
    try:
        response = requests.get(f"{API_BASE_URL}/predictions/status")
        if response.status_code == 200:
            print("✅ Status check passed!")
            status = response.json()
            print(f"   Pregame Service: {status.get('pregame_service')}")
            print(f"   Halftime Service: {status.get('halftime_service')}")
            print(f"   API Configured: {status.get('sportsdata_api_configured')}")
            print(f"   Supported Sports: {', '.join(status.get('supported_sports', []))}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status check error: {e}")
    
    # Test 3: Trigger Pregame Predictions
    print("\n3️⃣ Testing Pregame Predictions...")
    try:
        # Trigger the prediction
        params = {"sport": SPORT, "date": DATE, "tier": TIER}
        response = requests.post(f"{API_BASE_URL}/predictions/pregame", params=params)
        
        if response.status_code == 200:
            print("✅ Pregame prediction triggered!")
            result = response.json()
            print(f"   Message: {result.get('message')}")
            print(f"   Status: {result.get('status')}")
            
            # Wait a moment for processing
            print("   ⏳ Waiting 3 seconds for processing...")
            time.sleep(3)
            
            # Get the predictions
            get_response = requests.get(f"{API_BASE_URL}/predictions/pregame/{SPORT}", params={"date": DATE, "tier": TIER})
            if get_response.status_code == 200:
                print("✅ Retrieved pregame predictions!")
                predictions = get_response.json()
                analysis = predictions.get('data', {}).get('analysis', {})
                print(f"   Total Games: {analysis.get('total_games', 'N/A')}")
                print(f"   Total Props: {analysis.get('total_props', 'N/A')}")
                print(f"   High Confidence Props: {analysis.get('high_confidence_props', 'N/A')}")
                print(f"   Generated Parlays: {analysis.get('generated_parlays', 'N/A')}")
            else:
                print(f"❌ Failed to retrieve predictions: {get_response.status_code}")
        else:
            print(f"❌ Failed to trigger pregame predictions: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Pregame prediction error: {e}")
    
    # Test 4: Trigger Halftime Predictions
    print("\n4️⃣ Testing Halftime Predictions...")
    try:
        # Trigger the prediction
        params = {"sport": SPORT, "tier": TIER}
        response = requests.post(f"{API_BASE_URL}/predictions/halftime", params=params)
        
        if response.status_code == 200:
            print("✅ Halftime prediction triggered!")
            result = response.json()
            print(f"   Message: {result.get('message')}")
            print(f"   Status: {result.get('status')}")
            
            # Wait a moment for processing
            print("   ⏳ Waiting 3 seconds for processing...")
            time.sleep(3)
            
            # Get the predictions
            get_response = requests.get(f"{API_BASE_URL}/predictions/halftime/{SPORT}", params={"tier": TIER})
            if get_response.status_code == 200:
                print("✅ Retrieved halftime predictions!")
                predictions = get_response.json()
                analysis = predictions.get('data', {}).get('analysis', {})
                print(f"   Live Games: {analysis.get('live_games', 'N/A')}")
                print(f"   Live Props: {analysis.get('live_props', 'N/A')}")
                print(f"   High Confidence Plays: {analysis.get('high_confidence_plays', 'N/A')}")
                print(f"   Generated Parlays: {analysis.get('generated_parlays', 'N/A')}")
            else:
                print(f"❌ Failed to retrieve halftime predictions: {get_response.status_code}")
        else:
            print(f"❌ Failed to trigger halftime predictions: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Halftime prediction error: {e}")
    
    # Test 5: Legacy Endpoints
    print("\n5️⃣ Testing Legacy Endpoints...")
    try:
        # Test parlays endpoint
        response = requests.get(f"{API_BASE_URL}/parlays", params={"sport": SPORT})
        if response.status_code == 200:
            print("✅ Parlays endpoint working!")
            parlays = response.json()
            print(f"   Retrieved {len(parlays)} parlays")
        else:
            print(f"❌ Parlays endpoint failed: {response.status_code}")
        
        # Test stats endpoint
        stats_response = requests.get(f"{API_BASE_URL}/stats")
        if stats_response.status_code == 200:
            print("✅ Stats endpoint working!")
        else:
            print(f"❌ Stats endpoint failed: {stats_response.status_code}")
            
    except Exception as e:
        print(f"❌ Legacy endpoints error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 API Testing Complete!")

def demonstrate_api_usage():
    """Demonstrate practical API usage scenarios"""
    print("\n📚 API Usage Examples")
    print("=" * 50)
    
    print("\n🎯 Scenario 1: Daily Pregame Analysis")
    print("Use case: Get comprehensive pregame predictions for today's NFL games")
    print(f"Command: curl -X POST '{API_BASE_URL}/predictions/pregame?sport=NFL&tier=Premium'")
    print(f"Then: curl '{API_BASE_URL}/predictions/pregame/NFL?tier=Premium'")
    
    print("\n🎯 Scenario 2: Live Game Monitoring")
    print("Use case: Monitor live games and get halftime predictions")
    print(f"Command: curl -X POST '{API_BASE_URL}/predictions/halftime?sport=NFL&tier=GOAT'")
    print(f"Then: curl '{API_BASE_URL}/predictions/halftime/NFL?tier=GOAT'")
    
    print("\n🎯 Scenario 3: Specific Game Analysis")
    print("Use case: Analyze a specific live game")
    print(f"Command: curl -X POST '{API_BASE_URL}/predictions/halftime?sport=NFL&game_id=12345'")
    print(f"Then: curl '{API_BASE_URL}/predictions/halftime/NFL?game_id=12345'")
    
    print("\n🎯 Scenario 4: Multi-Sport Analysis")
    print("Use case: Run predictions for all major sports")
    for sport in ["NFL", "NBA", "MLB", "NHL"]:
        print(f"curl -X POST '{API_BASE_URL}/predictions/pregame?sport={sport}&tier=Premium'")
    
    print("\n🎯 Scenario 5: System Monitoring")
    print("Use case: Check system health and status")
    print(f"Health: curl '{API_BASE_URL}/health'")
    print(f"Status: curl '{API_BASE_URL}/predictions/status'")
    print(f"Stats: curl '{API_BASE_URL}/stats'")

def main():
    """Main function"""
    print("🚀 Stats Sync API Example & Test Script")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print(f"🏈 Test Sport: {SPORT}")
    print(f"📅 Test Date: {DATE}")
    print(f"🏆 Test Tier: {TIER}")
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running and accessible!")
        else:
            print(f"❌ API is not responding correctly: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure the API is running on http://localhost:8000")
        print("Start it with: python start_server.py")
        return
    
    # Run tests
    test_api_endpoints()
    
    # Show usage examples
    demonstrate_api_usage()

if __name__ == "__main__":
    main()
