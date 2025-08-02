"""
Parlay Optimizer FastAPI Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import logging
from dotenv import load_dotenv

# Import routes
from routes.generate_parlay_tier import router as tier_router
from routes.generate_parlay_custom import router as custom_router

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Parlay Optimizer API...")
    
    # Verify required environment variables
    required_vars = ["SPORTSDATAIO_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise RuntimeError(f"Missing environment variables: {missing_vars}")
    
    logger.info("Environment variables validated")
    logger.info("Parlay Optimizer API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Parlay Optimizer API...")

# Create FastAPI app
app = FastAPI(
    title="Parlay Optimizer API",
    description="Generate optimized sports parlays based on target payouts or custom odds",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tier_router, prefix="/api/v1", tags=["Tier Parlays"])
app.include_router(custom_router, prefix="/api/v1", tags=["Custom Parlays"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Parlay Optimizer API",
        "version": "1.0.0",
        "description": "Generate optimized sports parlays",
        "endpoints": {
            "tier_parlay": "/api/v1/generate-tier-parlay",
            "custom_parlay": "/api/v1/generate-custom-parlay",
            "health": "/health",
            "docs": "/docs"
        },
        "supported_sports": ["MLB", "NFL", "NBA", "NHL"],
        "tiers": ["$100", "$500", "$1000", "$5000", "$10000"],
        "risk_levels": ["low", "med", "high"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("SPORTSDATAIO_API_KEY")),
        "timestamp": "2025-07-31T00:00:00Z"
    }

@app.get("/api/v1/tiers")
async def get_available_tiers():
    """Get available payout tiers"""
    return {
        "tiers": [
            {"tier": "$100", "target_payout": 100.0, "description": "Entry level parlay"},
            {"tier": "$500", "target_payout": 500.0, "description": "Mid-tier parlay"},
            {"tier": "$1000", "target_payout": 1000.0, "description": "High-value parlay"},
            {"tier": "$5000", "target_payout": 5000.0, "description": "Premium parlay"},
            {"tier": "$10000", "target_payout": 10000.0, "description": "Elite parlay"}
        ]
    }

@app.get("/api/v1/sports")
async def get_supported_sports():
    """Get supported sports and their prop types"""
    return {
        "sports": {
            "mlb": {
                "name": "Major League Baseball",
                "prop_types": ["hits", "home_runs", "rbis", "strikeouts"],
                "season": "April - October"
            },
            "nfl": {
                "name": "National Football League", 
                "prop_types": ["passing_yards", "rushing_yards", "receiving_yards", "touchdowns", "receptions"],
                "season": "September - February"
            },
            "nba": {
                "name": "National Basketball Association",
                "prop_types": ["points", "assists", "rebounds"],
                "season": "October - June"
            },
            "nhl": {
                "name": "National Hockey League",
                "prop_types": ["goals", "assists", "shots"],
                "season": "October - June"
            }
        }
    }

@app.get("/api/v1/risk-levels")
async def get_risk_levels():
    """Get available risk levels and their characteristics"""
    return {
        "risk_levels": {
            "low": {
                "description": "Conservative approach with high hit rates",
                "min_hit_rate": "85%+",
                "typical_confidence": "80-95%",
                "parlay_size": "2-4 legs",
                "recommended_for": "Steady income, lower variance"
            },
            "med": {
                "description": "Balanced risk/reward approach",
                "min_hit_rate": "75%+", 
                "typical_confidence": "60-80%",
                "parlay_size": "3-6 legs",
                "recommended_for": "Moderate betting, good balance"
            },
            "high": {
                "description": "Aggressive approach for higher payouts",
                "min_hit_rate": "60%+",
                "typical_confidence": "40-60%",
                "parlay_size": "5+ legs",
                "recommended_for": "High-risk tolerance, big potential wins"
            }
        }
    }

# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    @app.get("/app")
    async def serve_frontend():
        """Serve the frontend application"""
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    logger.warning("Frontend directory not found - frontend serving disabled")

# Updated endpoints to match frontend expectations
@app.post("/generate/tier")
async def generate_tier_parlay_frontend(request: dict):
    """Generate tier-based parlay (frontend endpoint)"""
    from models.parlay_schema import TierParlayRequest, SportType, ParlayTier
    from routes.generate_parlay_tier import generate_tier_parlay
    
    try:
        # Convert bet amount to tier
        bet_amount = request.get("bet_amount", 100)
        if bet_amount <= 100:
            tier = ParlayTier.TIER_100
        elif bet_amount <= 500:
            tier = ParlayTier.TIER_500
        elif bet_amount <= 1000:
            tier = ParlayTier.TIER_1000
        elif bet_amount <= 5000:
            tier = ParlayTier.TIER_5000
        else:
            tier = ParlayTier.TIER_10000
        
        # Convert frontend request to proper schema
        sport_type = SportType(request.get("sport", "MLB").lower())
        tier_request = TierParlayRequest(
            tier=tier,
            sport=sport_type
        )
        
        response = await generate_tier_parlay(tier_request)
        
        # Convert response to frontend format
        return {
            "legs": response.parlay.legs,
            "total_odds": f"+{response.parlay.total_odds}",
            "confidence_score": response.parlay.confidence_score,
            "potential_payout": response.parlay.estimated_payout * (bet_amount / 10),  # Scale from $10 base
            "recommendation": f"Confidence: {response.parlay.confidence_score:.1f}% - {response.parlay.risk_level.value.title()} risk",
            "tier": tier.value,
            "sport": sport_type.value,
            "hit_probability": response.parlay.hit_probability
        }
        
    except Exception as e:
        logger.error(f"Error generating tier parlay: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/custom")
async def generate_custom_parlay_frontend(request: dict):
    """Generate custom parlay (frontend endpoint)"""
    from models.parlay_schema import CustomParlayRequest, SportType, RiskLevel
    from routes.generate_parlay_custom import generate_custom_parlay
    
    try:
        # Convert target odds string to integer
        target_odds_str = request.get("target_odds", "+2500")
        target_odds = int(target_odds_str.replace("+", "").replace("-", ""))
        
        # Convert frontend request to proper schema
        sport_type = SportType(request.get("sport", "MLB").lower())
        
        # Map risk_tolerance to risk_level
        risk_tolerance = request.get("risk_tolerance", "moderate").lower()
        if risk_tolerance == "conservative":
            risk_level = RiskLevel.LOW
        elif risk_tolerance == "aggressive":
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.MEDIUM
        
        custom_request = CustomParlayRequest(
            target_odds=target_odds,
            risk_level=risk_level,
            sport=sport_type
        )
        
        response = await generate_custom_parlay(custom_request)
        
        # Convert response to frontend format
        return {
            "legs": response.parlay.legs,
            "total_odds": f"+{response.actual_odds}",
            "confidence_score": response.parlay.confidence_score,
            "potential_payout": response.parlay.estimated_payout * 10,  # Scale from $10 base
            "recommendation": f"Confidence: {response.parlay.confidence_score:.1f}% - {response.parlay.risk_level.value.title()} risk",
            "target_odds": f"+{response.target_odds}",
            "actual_odds": f"+{response.actual_odds}",
            "sport": sport_type.value,
            "hit_probability": response.parlay.hit_probability
        }
        
    except Exception as e:
        logger.error(f"Error generating custom parlay: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8002))  # Different port to avoid conflicts
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
