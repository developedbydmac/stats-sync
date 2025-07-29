import os
from datetime import datetime
from typing import Optional
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.services.discord_service import DiscordService
from src.utils.logger import setup_logger

logger = setup_logger()

class SchedulerService:
    """Service for handling scheduled tasks like parlay refreshes and Discord notifications"""
    
    def __init__(self, parlay_service):
        self.parlay_service = parlay_service
        self.discord_service = DiscordService()
        self.scheduler = AsyncIOScheduler()
        self.refresh_interval = int(os.getenv("REFRESH_INTERVAL_MINUTES", "10"))
        self.is_running = False
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            return
        
        try:
            # Schedule parlay refresh every N minutes
            self.scheduler.add_job(
                self._refresh_and_notify,
                IntervalTrigger(minutes=self.refresh_interval),
                id="parlay_refresh",
                name="Refresh Parlays and Send Notifications",
                replace_existing=True
            )
            
            # Schedule daily cleanup at 2 AM
            self.scheduler.add_job(
                self._daily_cleanup,
                "cron",
                hour=2,
                minute=0,
                id="daily_cleanup",
                name="Daily Cleanup",
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info(f"Scheduler started with {self.refresh_interval}-minute refresh interval")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
            raise
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
    
    async def _refresh_and_notify(self):
        """Refresh parlays and send Discord notifications"""
        try:
            logger.info("Starting scheduled parlay refresh...")
            
            # Refresh parlays for all sports
            await self.parlay_service.refresh_all_parlays()
            
            # Send Discord notifications for new parlays
            await self._send_discord_notifications()
            
            logger.info("Scheduled parlay refresh completed successfully")
            
        except Exception as e:
            logger.error(f"Error in scheduled refresh: {str(e)}")
    
    async def _send_discord_notifications(self):
        """Send Discord notifications for new high-confidence parlays"""
        try:
            from src.models.parlay import SportType, TierType
            
            # Get GOAT tier parlays for notification
            for sport in SportType:
                goat_parlays = await self.parlay_service.get_parlays(sport, TierType.GOAT)
                
                for parlay_response in goat_parlays:
                    parlay = parlay_response.parlay
                    
                    # Only notify for very high confidence parlays
                    if parlay.overall_confidence >= 97:
                        await self.discord_service.send_parlay_notification(parlay_response)
                        
                        # Add delay to avoid rate limiting
                        await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error sending Discord notifications: {str(e)}")
    
    async def _daily_cleanup(self):
        """Perform daily cleanup tasks"""
        try:
            logger.info("Starting daily cleanup...")
            
            # Clear old parlay cache
            self.parlay_service.parlay_cache.clear()
            
            # Log system statistics
            stats = await self.parlay_service.get_system_stats()
            logger.info(f"Daily stats - Total parlays: {stats.total_parlays_generated}")
            
            # Reset daily counters
            self.parlay_service.stats["total_parlays_generated"] = 0
            self.parlay_service.stats["successful_requests"] = 0
            self.parlay_service.stats["failed_requests"] = 0
            self.parlay_service.stats["cache_hits"] = 0
            
            logger.info("Daily cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in daily cleanup: {str(e)}")
    
    def trigger_manual_refresh(self):
        """Trigger a manual refresh outside of the scheduled time"""
        if self.is_running:
            self.scheduler.add_job(
                self._refresh_and_notify,
                "date",
                run_date=datetime.now(),
                id="manual_refresh",
                name="Manual Refresh",
                replace_existing=True
            )
            logger.info("Manual refresh triggered")
        else:
            logger.warning("Cannot trigger manual refresh - scheduler not running")
    
    def get_next_refresh_time(self) -> Optional[datetime]:
        """Get the next scheduled refresh time"""
        if not self.is_running:
            return None
            
        job = self.scheduler.get_job("parlay_refresh")
        return job.next_run_time if job else None
    
    def get_scheduler_status(self) -> dict:
        """Get current scheduler status"""
        return {
            "running": self.is_running,
            "refresh_interval_minutes": self.refresh_interval,
            "next_refresh": self.get_next_refresh_time(),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time
                }
                for job in self.scheduler.get_jobs()
            ] if self.is_running else []
        }
