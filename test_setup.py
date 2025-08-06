#!/usr/bin/env python3
"""
Quick test script to verify the FastAPI app with prediction services
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all services can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from dotenv import load_dotenv
        print("✅ dotenv imported")
        
        from src.services.pregame_prediction_service import PregamePredictionService
        print("✅ PregamePredictionService imported")
        
        from src.services.halftime_prediction_service import HalftimePredictionService
        print("✅ HalftimePredictionService imported")
        
        from src.models.parlay import SportType, TierType
        print("✅ SportType and TierType imported")
        
        print("\n🎯 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_env_config():
    """Test environment configuration"""
    print("\n🔧 Testing environment configuration...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("SPORTSDATA_API_KEY")
    if api_key:
        print(f"✅ SportsDataIO API Key found: {api_key[:8]}...")
    else:
        print("⚠️  SportsDataIO API Key not found (will use mock data)")
    
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    debug = os.getenv("DEBUG", "True")
    
    print(f"✅ Host: {host}")
    print(f"✅ Port: {port}")
    print(f"✅ Debug: {debug}")

def test_prediction_services():
    """Test prediction service initialization"""
    print("\n🔮 Testing prediction services...")
    
    try:
        from src.services.pregame_prediction_service import PregamePredictionService
        from src.services.halftime_prediction_service import HalftimePredictionService
        
        pregame_service = PregamePredictionService()
        print("✅ Pregame service initialized")
        
        halftime_service = HalftimePredictionService()
        print("✅ Halftime service initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Service initialization error: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI app creation"""
    print("\n🚀 Testing FastAPI app...")
    
    try:
        from main import app
        print("✅ FastAPI app imported successfully")
        
        # Test that the app has our new routes
        routes = [route.path for route in app.routes]
        
        prediction_routes = [
            "/predictions/pregame",
            "/predictions/halftime/{sport}",
            "/predictions/status"
        ]
        
        for route in prediction_routes:
            if any(route in r for r in routes):
                print(f"✅ Route found: {route}")
            else:
                print(f"❌ Route missing: {route}")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Stats Sync API - Prediction Services Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 4
    
    if test_imports():
        tests_passed += 1
    
    test_env_config()  # Always run for info
    
    if test_prediction_services():
        tests_passed += 1
    
    if test_fastapi_app():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The API is ready to run.")
        print("\n🚀 To start the server:")
        print("   python start_server.py")
        print("\n📚 To test the API:")
        print("   python test_api.py")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
