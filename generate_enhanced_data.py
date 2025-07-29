#!/usr/bin/env python3
"""Enhanced historical data generator for better test coverage"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_enhanced_historical_data():
    """Generate historical data with varied hit rates for better tier coverage"""
    
    # Define players with different expected performance levels
    high_performers = [
        ("Josh Allen", "passing_yards", 0.85),  # 85% hit rate for Premium tier
        ("Patrick Mahomes", "passing_yards", 0.82),
        ("Stefon Diggs", "receiving_yards", 0.88),
        ("Travis Kelce", "receiving_yards", 0.90),
        ("Christian McCaffrey", "rushing_yards", 0.87),
    ]
    
    premium_performers = [
        ("Lamar Jackson", "passing_yards", 0.75),
        ("Derrick Henry", "rushing_yards", 0.78),
        ("Tyreek Hill", "receiving_yards", 0.80),
        ("Cooper Kupp", "receptions", 0.76),
        ("Justin Jefferson", "receptions", 0.82),
    ]
    
    goat_performers = [
        ("Aaron Rodgers", "passing_yards", 0.96),  # GOAT tier
        ("Davante Adams", "receptions", 0.97),
        ("Saquon Barkley", "rushing_yards", 0.95),
    ]
    
    # Generate data for MLB players too
    mlb_high_performers = [
        ("Aaron Judge", "home_runs", 0.85),
        ("Mookie Betts", "hits", 0.88),
        ("Ronald Acuña Jr.", "hits", 0.86),
        ("Gerrit Cole", "strikeouts", 0.90),
        ("Vladimir Guerrero Jr.", "total_bases", 0.82),
    ]
    
    mlb_goat_performers = [
        ("Juan Soto", "hits", 0.96),
        ("Shane Bieber", "strikeouts", 0.97),
    ]
    
    all_performers = high_performers + premium_performers + goat_performers + mlb_high_performers + mlb_goat_performers
    
    records = []
    base_date = datetime.now() - timedelta(days=60)  # Start 60 days ago to ensure recent data
    
    for player_name, prop_type, target_hit_rate in all_performers:
        sport = "MLB" if prop_type in ["home_runs", "hits", "strikeouts", "total_bases", "rbis"] else "NFL"
        
        # Generate 30 historical records per player
        for i in range(30):
            date = base_date + timedelta(days=i * 7)  # Weekly games
            
            # Set realistic lines based on prop type
            if prop_type == "passing_yards":
                line = random.uniform(225, 300)
                actual = random.uniform(180, 380)
            elif prop_type == "receiving_yards":
                line = random.uniform(60, 90)
                actual = random.uniform(30, 140)
            elif prop_type == "rushing_yards":
                line = random.uniform(75, 120)
                actual = random.uniform(40, 180)
            elif prop_type == "receptions":
                line = random.uniform(5.5, 8.5)
                actual = random.uniform(3, 12)
            elif prop_type == "passing_touchdowns":
                line = random.uniform(1.5, 2.5)
                actual = random.uniform(0, 4)
            elif prop_type == "home_runs":
                line = 0.5
                actual = random.choice([0, 1, 2])
            elif prop_type == "hits":
                line = 1.5
                actual = random.choice([0, 1, 2, 3])
            elif prop_type == "strikeouts":
                line = random.uniform(6.5, 9.5)
                actual = random.uniform(3, 14)
            elif prop_type == "total_bases":
                line = random.uniform(1.5, 3.5)
                actual = random.uniform(0, 6)
            else:
                line = random.uniform(1.5, 2.5)
                actual = random.uniform(0, 4)
            
            # Determine hit based on target hit rate
            hit = random.random() < target_hit_rate
            
            # Adjust actual result to match hit outcome
            if hit and actual < line:
                actual = line + random.uniform(0.1, 20)
            elif not hit and actual > line:
                actual = line - random.uniform(0.1, 15)
            
            records.append({
                "player_name": player_name,
                "date": date.strftime("%Y-%m-%d"),
                "prop_type": prop_type,
                "line": round(line, 1),
                "actual_result": round(actual, 1),
                "hit": hit,
                "odds": random.choice([-105, -110, -115, -120, +100, +105]),
                "sport": sport
            })
    
    # Create DataFrame and save
    df = pd.DataFrame(records)
    df.to_csv("data/historical_props.csv", index=False)
    
    print(f"Generated {len(records)} historical records")
    print("Hit rate distribution:")
    hit_rates = df.groupby('player_name')['hit'].mean().sort_values(ascending=False)
    print(hit_rates.head(10))

if __name__ == "__main__":
    generate_enhanced_historical_data()
