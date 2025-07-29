from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import logging
from contextlib import asynccontextmanager

from src.models.parlay import ParlayResponse, SportType, TierType
from src.services.parlay_service import ParlayService
from src.services.scheduler_service import SchedulerService
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger()

# Global services
parlay_service = None
scheduler_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global parlay_service, scheduler_service
    
    # Startup
    logger.info("Starting Stats Sync API...")
    parlay_service = ParlayService()
    scheduler_service = SchedulerService(parlay_service)
    scheduler_service.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Stats Sync API...")
    if scheduler_service:
        scheduler_service.stop()

app = FastAPI(
    title="Stats Sync API",
    description="Real-time sports parlay generation with confidence scoring",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "stats-sync-api"}

@app.get("/parlays", response_model=List[ParlayResponse])
async def get_parlays(
    sport: SportType = SportType.NFL,
    tier: TierType = None,
    refresh: bool = False
):
    """
    Get parlays for a specific sport and tier
    
    Args:
        sport: Sport type (MLB or NFL)
        tier: Optional tier filter (Free, Premium, GOAT)
        refresh: Force refresh of data
    
    Returns:
        List of parlays matching the criteria
    """
    try:
        if refresh:
            logger.info(f"Force refreshing parlays for {sport.value}")
            await parlay_service.refresh_parlays(sport)
        
        parlays = await parlay_service.get_parlays(sport, tier)
        logger.info(f"Retrieved {len(parlays)} parlays for {sport.value}")
        return parlays
        
    except Exception as e:
        logger.error(f"Error retrieving parlays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving parlays: {str(e)}")

@app.post("/parlays/refresh")
async def refresh_parlays(background_tasks: BackgroundTasks, sport: SportType = None):
    """
    Manually trigger parlay refresh
    
    Args:
        sport: Optional sport to refresh (if not provided, refreshes all)
    """
    try:
        if sport:
            background_tasks.add_task(parlay_service.refresh_parlays, sport)
            message = f"Refresh triggered for {sport.value}"
        else:
            background_tasks.add_task(parlay_service.refresh_all_parlays)
            message = "Refresh triggered for all sports"
        
        logger.info(message)
        return {"message": message}
        
    except Exception as e:
        logger.error(f"Error triggering refresh: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error triggering refresh: {str(e)}")

@app.get("/props/{sport}")
async def get_player_props(sport: SportType, date: str = None):
    """
    Get real-time player props for a sport
    
    Args:
        sport: Sport type (MLB or NFL)
        date: Optional date (YYYY-MM-DD format)
    
    Returns:
        Raw player props data
    """
    try:
        props = await parlay_service.get_player_props(sport, date)
        return {"sport": sport.value, "date": date, "props": props}
        
    except Exception as e:
        logger.error(f"Error retrieving props: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving props: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        stats = await parlay_service.get_system_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
