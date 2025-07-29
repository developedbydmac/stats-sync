import pandas as pd
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from src.models.parlay import HistoricalProp, PropType, SportType, ConfidenceFactors

logger = logging.getLogger("stats-sync")

class PropAnalyzer:
    """Analyzes historical prop data to calculate hit rates and confidence scores"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.historical_data: Optional[pd.DataFrame] = None
        self.load_historical_data()
    
    def load_historical_data(self):
        """Load historical prop data from CSV"""
        try:
            if os.path.exists(self.csv_path):
                self.historical_data = pd.read_csv(self.csv_path)
                logger.info(f"Loaded {len(self.historical_data)} historical prop records")
            else:
                logger.warning(f"Historical data file not found: {self.csv_path}")
                # Create sample data for development
                self.create_sample_data()
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
            self.create_sample_data()
    
    def create_sample_data(self):
        """Create sample historical data for development"""
        sample_data = [
            {"player_name": "Patrick Mahomes", "date": "2023-12-01", "prop_type": "passing_yards", 
             "line": 275.5, "actual_result": 320, "hit": True, "odds": -110, "sport": "NFL"},
            {"player_name": "Josh Allen", "date": "2023-12-01", "prop_type": "passing_yards", 
             "line": 250.5, "actual_result": 240, "hit": False, "odds": -110, "sport": "NFL"},
            {"player_name": "Tua Tagovailoa", "date": "2023-12-01", "prop_type": "passing_yards", 
             "line": 225.5, "actual_result": 280, "hit": True, "odds": -110, "sport": "NFL"},
            {"player_name": "Aaron Judge", "date": "2023-09-15", "prop_type": "home_runs", 
             "line": 0.5, "actual_result": 1, "hit": True, "odds": +150, "sport": "MLB"},
            {"player_name": "Mookie Betts", "date": "2023-09-15", "prop_type": "hits", 
             "line": 1.5, "actual_result": 2, "hit": True, "odds": -120, "sport": "MLB"},
        ]
        
        self.historical_data = pd.DataFrame(sample_data)
        logger.info("Created sample historical data for development")
    
    def get_player_hit_rate(self, player_name: str, prop_type: PropType, 
                           days_back: int = 30) -> float:
        """
        Calculate hit rate for a specific player and prop type
        
        Args:
            player_name: Player name
            prop_type: Type of prop
            days_back: Number of days to look back
            
        Returns:
            Hit rate as a decimal (0.0 to 1.0)
        """
        if self.historical_data is None or len(self.historical_data) == 0:
            return 0.5  # Default neutral hit rate
        
        # Filter data
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered_data = self.historical_data[
            (self.historical_data['player_name'] == player_name) &
            (self.historical_data['prop_type'] == prop_type.value) &
            (pd.to_datetime(self.historical_data['date']) >= cutoff_date)
        ]
        
        if len(filtered_data) == 0:
            # Fall back to overall prop type hit rate
            prop_data = self.historical_data[
                (self.historical_data['prop_type'] == prop_type.value) &
                (pd.to_datetime(self.historical_data['date']) >= cutoff_date)
            ]
            if len(prop_data) > 0:
                return prop_data['hit'].mean()
            return 0.5
        
        return filtered_data['hit'].mean()
    
    def get_recent_performance(self, player_name: str, prop_type: PropType, 
                              games_back: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent performance data for a player
        
        Args:
            player_name: Player name
            prop_type: Type of prop
            games_back: Number of recent games to return
            
        Returns:
            List of recent performance data
        """
        if self.historical_data is None:
            return []
        
        recent_data = self.historical_data[
            (self.historical_data['player_name'] == player_name) &
            (self.historical_data['prop_type'] == prop_type.value)
        ].sort_values('date', ascending=False).head(games_back)
        
        return recent_data.to_dict('records')
    
    def calculate_confidence_score(self, player_name: str, prop_type: PropType,
                                 line: float, recent_games: int = 10) -> float:
        """
        Calculate confidence score for a prop based on multiple factors
        
        Args:
            player_name: Player name
            prop_type: Type of prop
            line: Current prop line
            recent_games: Number of recent games to analyze
            
        Returns:
            Confidence score from 0 to 100
        """
        factors = ConfidenceFactors(
            historical_hit_rate=self.get_player_hit_rate(player_name, prop_type, 90),
            recent_form_weight=self.get_recent_form_weight(player_name, prop_type, recent_games),
            injury_factor=1.0,  # Would be populated from injury data
            weather_factor=1.0,  # Would be populated from weather data
            matchup_factor=1.0,  # Would be populated from matchup analysis
            line_movement_factor=1.0  # Would be populated from line movement data
        )
        
        # Base confidence from historical hit rate
        base_confidence = factors.historical_hit_rate * 100
        
        # Adjust for recent form (±20 points max)
        recent_adjustment = (factors.recent_form_weight - 0.5) * 40
        
        # Apply other factors (multiplicative)
        final_confidence = (base_confidence + recent_adjustment) * \
                          factors.injury_factor * \
                          factors.weather_factor * \
                          factors.matchup_factor * \
                          factors.line_movement_factor
        
        # Clamp between 0 and 100
        return max(0, min(100, final_confidence))
    
    def get_recent_form_weight(self, player_name: str, prop_type: PropType, 
                              games_back: int = 5) -> float:
        """Calculate recent form weight (higher = better recent performance)"""
        recent_performance = self.get_recent_performance(player_name, prop_type, games_back)
        
        if not recent_performance:
            return 0.5  # Neutral
        
        # Calculate weighted average with more recent games having higher weight
        total_weight = 0
        weighted_sum = 0
        
        for i, game in enumerate(recent_performance):
            weight = games_back - i  # More recent = higher weight
            weighted_sum += game.get('hit', 0) * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
