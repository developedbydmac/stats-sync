import os
import aiohttp
import json
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from src.models.parlay import ParlayResponse, TierType
from src.utils.logger import setup_logger

logger = setup_logger()

class DiscordService:
    """Service for sending Discord webhook notifications"""
    
    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.webhook_url:
            logger.warning("DISCORD_WEBHOOK_URL not found in environment variables")
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close_session(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def send_parlay_notification(self, parlay_response: ParlayResponse):
        """
        Send a Discord notification for a new high-confidence parlay
        
        Args:
            parlay_response: Parlay response to notify about
        """
        if not self.webhook_url:
            logger.debug("Discord webhook not configured, skipping notification")
            return
        
        try:
            embed = self._create_parlay_embed(parlay_response)
            
            payload = {
                "content": self._get_notification_content(parlay_response),
                "embeds": [embed]
            }
            
            session = await self.get_session()
            async with session.post(self.webhook_url, json=payload) as response:
                if response.status == 204:
                    logger.info(f"Discord notification sent for {parlay_response.parlay.tier.value} parlay")
                else:
                    logger.error(f"Discord webhook failed with status {response.status}")
                    
        except Exception as e:
            logger.error(f"Error sending Discord notification: {str(e)}")
    
    def _get_notification_content(self, parlay_response: ParlayResponse) -> str:
        """Get the main notification content"""
        parlay = parlay_response.parlay
        
        if parlay.tier == TierType.GOAT:
            return f"🐐 **GOAT TIER ALERT** 🐐\n**{parlay.overall_confidence:.1f}% Confidence** - This is the play!"
        elif parlay.tier == TierType.PREMIUM:
            return f"💎 **Premium Play Available** 💎\n**{parlay.overall_confidence:.1f}% Confidence** - High value detected!"
        else:
            return f"⚡ **New Free Play** ⚡\n**{parlay.overall_confidence:.1f}% Confidence** - Solid value bet!"
    
    def _create_parlay_embed(self, parlay_response: ParlayResponse) -> Dict[str, Any]:
        """Create Discord embed for the parlay"""
        parlay = parlay_response.parlay
        analysis = parlay_response.analysis
        
        # Color based on tier
        color = {
            TierType.GOAT: 0xFFD700,    # Gold
            TierType.PREMIUM: 0x9932CC,  # Purple
            TierType.FREE: 0x1E90FF     # Blue
        }.get(parlay.tier, 0x1E90FF)
        
        # Build fields for each leg
        fields = []
        
        # Parlay overview
        fields.append({
            "name": "📊 Parlay Overview",
            "value": (
                f"**Sport:** {parlay.sport.value}\n"
                f"**Legs:** {len(parlay.legs)}\n"
                f"**Total Odds:** {self._format_odds(parlay.total_odds)}\n"
                f"**Expected Payout:** {parlay.expected_payout:.1f}x"
            ),
            "inline": True
        })
        
        # Analysis
        fields.append({
            "name": "🎯 Analysis",
            "value": (
                f"**Confidence:** {parlay.overall_confidence:.1f}%\n"
                f"**Hit Rate:** {analysis['expected_hit_rate']:.1%}\n"
                f"**Risk:** {analysis['risk_assessment']}\n"
                f"**Recommendation:** {analysis['recommendation'][:50]}..."
            ),
            "inline": True
        })
        
        # Top legs (show first 3)
        top_legs = sorted(parlay.legs, key=lambda x: x.confidence, reverse=True)[:3]
        legs_text = ""
        for i, leg in enumerate(top_legs, 1):
            prop = leg.player_prop
            legs_text += (
                f"**{i}.** {prop.player_name} ({prop.team})\n"
                f"   {prop.prop_type.value.replace('_', ' ').title()} "
                f"{leg.selection} {prop.line} ({self._format_odds(leg.odds)})\n"
                f"   Confidence: {leg.confidence:.1f}%\n\n"
            )
        
        if len(parlay.legs) > 3:
            legs_text += f"*+ {len(parlay.legs) - 3} more legs...*"
        
        fields.append({
            "name": f"🏈 Key Legs ({len(top_legs)} of {len(parlay.legs)})",
            "value": legs_text,
            "inline": False
        })
        
        # Footer with timestamp
        embed = {
            "title": parlay.description,
            "color": color,
            "fields": fields,
            "footer": {
                "text": f"Stats Sync • {datetime.now().strftime('%Y-%m-%d %H:%M')} EST"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return embed
    
    def _format_odds(self, odds: int) -> str:
        """Format odds for display"""
        if odds > 0:
            return f"+{odds}"
        else:
            return str(odds)
    
    async def send_system_alert(self, message: str, alert_type: str = "info"):
        """Send a system alert to Discord"""
        if not self.webhook_url:
            return
        
        try:
            color_map = {
                "info": 0x00FF00,     # Green
                "warning": 0xFFFF00,  # Yellow
                "error": 0xFF0000     # Red
            }
            
            embed = {
                "title": f"🤖 System Alert",
                "description": message,
                "color": color_map.get(alert_type, 0x00FF00),
                "timestamp": datetime.now().isoformat()
            }
            
            payload = {"embeds": [embed]}
            
            session = await self.get_session()
            async with session.post(self.webhook_url, json=payload) as response:
                if response.status == 204:
                    logger.info(f"System alert sent to Discord: {alert_type}")
                else:
                    logger.error(f"Failed to send system alert: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error sending system alert: {str(e)}")
    
    async def send_daily_summary(self, stats: Dict[str, Any]):
        """Send daily performance summary"""
        if not self.webhook_url:
            return
        
        try:
            embed = {
                "title": "📈 Daily Performance Summary",
                "description": "Here's how Stats Sync performed today:",
                "color": 0x00FF7F,  # Spring green
                "fields": [
                    {
                        "name": "📊 Generation Stats",
                        "value": (
                            f"**Parlays Generated:** {stats.get('total_parlays_generated', 0)}\n"
                            f"**Successful Requests:** {stats.get('successful_requests', 0)}\n"
                            f"**Cache Hit Rate:** {stats.get('cache_hit_rate', 0):.1%}"
                        ),
                        "inline": True
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            payload = {"embeds": [embed]}
            
            session = await self.get_session()
            async with session.post(self.webhook_url, json=payload) as response:
                if response.status == 204:
                    logger.info("Daily summary sent to Discord")
                    
        except Exception as e:
            logger.error(f"Error sending daily summary: {str(e)}")
