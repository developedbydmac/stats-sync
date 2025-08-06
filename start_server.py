#!/usr/bin/env python3
"""
Startup script for the Stats Sync API with SportsDataIO integration
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_environment():
    """Check if the environment is properly configured"""
    required_env_vars = ["SPORTSDATA_API_KEY"]
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all required variables are set.")
        return False
    
    print("✅ Environment configuration looks good!")
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Stats Sync API...")
    print("📊 Loading environment variables from .env file...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check environment configuration
    if not check_environment():
        sys.exit(1)
    
    # Display configuration
    api_key = os.getenv("SPORTSDATA_API_KEY")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"🔑 SportsDataIO API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
    print(f"🌐 Server will run on: http://{host}:{port}")
    print(f"🔧 Debug mode: {'Enabled' if debug else 'Disabled'}")
    print("\n📋 Available Endpoints:")
    print("  • GET  /health - Health check")
    print("  • GET  /predictions/status - Prediction services status")
    print("  • POST /predictions/pregame - Trigger pregame predictions")
    print("  • GET  /predictions/pregame/{sport} - Get pregame predictions")
    print("  • POST /predictions/halftime - Trigger halftime predictions")
    print("  • GET  /predictions/halftime/{sport} - Get halftime predictions")
    print("  • GET  /parlays - Get parlays for sport/tier")
    print("  • POST /parlays/refresh - Refresh parlay data")
    print("  • GET  /props/{sport} - Get player props")
    print("  • GET  /parlays/live - Get live/halftime parlays")
    print("  • GET  /stats - Get system statistics")
    
    print("\n🎯 Supported Sports: NFL, MLB, NBA, NHL")
    print("🏆 Supported Tiers: Free, Premium, GOAT")
    
    print("\n📡 Starting FastAPI server...")
    
    # Import and run the FastAPI app
    import uvicorn
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )

if __name__ == "__main__":
    main()
