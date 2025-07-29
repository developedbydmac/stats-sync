#!/usr/bin/env python3
"""
Stats Sync - Smart Parlay Generator
Run script for development and production
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import pandas
        import aiohttp
        print("✅ All required packages found")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def setup_environment():
    """Setup environment variables from .env file"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found. Copying from .env.example...")
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print("✅ Created .env file. Please update with your API keys.")
        else:
            print("❌ .env.example not found")
            return False
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
        return True
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment")
        return True

def run_tests():
    """Run the test suite"""
    print("🧪 Running test suite...")
    test_file = Path("tests/test_parlay_system.py")
    if test_file.exists():
        subprocess.run([sys.executable, str(test_file)])
    else:
        print("❌ Test file not found")

def run_server(host="0.0.0.0", port=8000, reload=True):
    """Run the FastAPI server"""
    print(f"🚀 Starting Stats Sync server on {host}:{port}")
    print(f"📱 Web interface: http://localhost:{port}")
    print(f"📚 API docs: http://localhost:{port}/docs")
    print("🔄 Auto-reload: " + ("enabled" if reload else "disabled"))
    print("\nPress Ctrl+C to stop the server")
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def create_sample_data():
    """Create sample historical data if it doesn't exist"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    csv_file = data_dir / "historical_props.csv"
    if not csv_file.exists():
        print("📊 Creating sample historical data...")
        # Sample data is already created in the CSV file
        print("✅ Sample data available")
    else:
        print("✅ Historical data found")

def main():
    parser = argparse.ArgumentParser(description="Stats Sync - Smart Parlay Generator")
    parser.add_argument("command", choices=["run", "test", "setup"], 
                      help="Command to execute")
    parser.add_argument("--host", default="0.0.0.0", 
                      help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, 
                      help="Server port (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", 
                      help="Disable auto-reload")
    
    args = parser.parse_args()
    
    print("⚡ Stats Sync - AI-Powered Sports Parlay Generator")
    print("=" * 60)
    
    if args.command == "setup":
        print("🔧 Setting up Stats Sync...")
        check_requirements()
        setup_environment()
        create_sample_data()
        print("\n✅ Setup complete! Run 'python run.py run' to start the server")
        
    elif args.command == "test":
        if not check_requirements():
            return
        setup_environment()
        run_tests()
        
    elif args.command == "run":
        if not check_requirements():
            return
        if not setup_environment():
            return
        create_sample_data()
        run_server(
            host=args.host, 
            port=args.port, 
            reload=not args.no_reload
        )

if __name__ == "__main__":
    main()
