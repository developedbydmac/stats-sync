#!/usr/bin/env python3
"""
Test script to validate Stats Sync API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_endpoint(endpoint, description):
    """Test an endpoint and print results"""
    print(f"\n🧪 Testing {description}")
    print(f"   URL: {BASE_URL}{endpoint}")
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Success: {response.status_code}")
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"   📊 Returned {len(data)} items")
                print(f"   📝 Sample: {json.dumps(data[0] if data else {}, indent=2)[:200]}...")
            elif isinstance(data, dict):
                print(f"   📝 Response: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")

def main():
    print("🚀 Stats Sync API - Endpoint Testing")
    print("=" * 50)
    
    # Test basic endpoints
    test_endpoint("/health", "Health Check")
    test_endpoint("/docs", "API Documentation")
    test_endpoint("/schedule", "NFL Schedule")
    
    # Test prediction endpoints (these will likely fail with real data but should show proper error handling)
    test_endpoint("/pregame/1234?prop_line=25.5", "Pregame Prediction (will likely 404 - that's expected)")
    test_endpoint("/liveprops/1234", "Live Props (will likely 404 - that's expected)")
    
    print("\n" + "=" * 50)
    print("🎯 API Testing Complete!")
    print("📋 Summary:")
    print("   • Health check should work ✅")
    print("   • Schedule endpoint should return NFL games ✅") 
    print("   • Docs should be accessible at /docs ✅")
    print("   • Prediction endpoints should show proper error handling ✅")
    print("\n💡 To test with real data, you need valid player/game IDs from the schedule")
    print("🌐 Visit http://localhost:8001/docs for interactive API documentation")

if __name__ == "__main__":
    main()
