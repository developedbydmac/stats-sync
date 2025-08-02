# Parlay Optimizer API

A FastAPI application for generating optimized sports parlays based on target payouts or custom odds using SportsDataIO player statistics.

## Features

- **Tier-Based Parlays**: Generate parlays targeting specific payout amounts ($100, $500, $1000, $5000, $10000)
- **Custom Odds Parlays**: Build parlays to hit specific odds targets (e.g. +2640)
- **Risk Level Control**: Choose between low, medium, and high risk approaches
- **Multi-Sport Support**: MLB, NFL, NBA, NHL
- **Real Player Data**: Uses SportsDataIO API for accurate player statistics and hit rates
- **Confidence Scoring**: Advanced algorithms calculate parlay confidence and hit probability

## Quick Start

1. **Install Dependencies**
   ```bash
   cd parlay-optimizer
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # Copy .env file and add your SportsDataIO API key
   # SPORTSDATAIO_API_KEY=your_api_key_here
   ```

3. **Run the Server**
   ```bash
   python main.py
   ```

4. **Test the API**
   ```bash
   python test_optimizer.py
   ```

## API Endpoints

### Tier-Based Parlay Generation

**POST** `/api/v1/generate-tier-parlay`

Generate a parlay targeting a specific payout tier.

**Request Body:**
```json
{
  "tier": "$500",
  "sport": "mlb",
  "max_legs": 6,
  "min_hit_rate": 0.8
}
```

**Response:**
```json
{
  "tier": "$500",
  "target_payout": 500.0,
  "parlay": {
    "legs": [
      {
        "prop": {
          "player_name": "Aaron Judge",
          "team": "NYY",
          "prop_type": "hits",
          "line": 0.5,
          "estimated_odds": 180,
          "hit_rate": 0.85,
          "confidence_score": 85.0
        },
        "selection": "over",
        "odds": 180,
        "confidence": 85.0
      }
    ],
    "total_odds": 2450,
    "estimated_payout": 255.0,
    "confidence_score": 78.5,
    "hit_probability": 0.234,
    "risk_level": "medium"
  },
  "analysis": {
    "target_payout": 500.0,
    "actual_payout": 255.0,
    "legs_count": 4,
    "average_hit_rate": 0.825
  }
}
```

### Custom Odds Parlay Generation

**POST** `/api/v1/generate-custom-parlay`

Generate a parlay targeting specific odds.

**Request Body:**
```json
{
  "target_odds": 2640,
  "risk_level": "med",
  "sport": "mlb",
  "max_legs": 8,
  "min_hit_rate": 0.7
}
```

**Response:**
```json
{
  "target_odds": 2640,
  "actual_odds": 2580,
  "parlay": {
    "legs": [...],
    "total_odds": 2580,
    "estimated_payout": 268.0,
    "confidence_score": 65.2,
    "hit_probability": 0.186,
    "risk_level": "med"
  },
  "odds_analysis": {
    "odds_accuracy": 0.977,
    "recommendation": "Good odds approximation | Moderate confidence - consider smaller bet | Risk level matches expectations"
  }
}
```

### Information Endpoints

- **GET** `/api/v1/tiers` - Available payout tiers
- **GET** `/api/v1/sports` - Supported sports and prop types  
- **GET** `/api/v1/risk-levels` - Risk level descriptions
- **GET** `/health` - API health check

## Configuration

### Environment Variables

```bash
# Required
SPORTSDATAIO_API_KEY=your_api_key_here

# Optional
DEBUG=True
HOST=0.0.0.0
PORT=8002
DEFAULT_BET_AMOUNT=10.0
MAX_PARLAY_LEGS=12
MIN_HIT_RATE=0.6
CONFIDENCE_THRESHOLD=60.0
```

### Supported Sports

- **MLB**: hits, home_runs, rbis, strikeouts
- **NFL**: passing_yards, rushing_yards, receiving_yards, touchdowns, receptions
- **NBA**: points, assists, rebounds
- **NHL**: goals, assists, shots

### Risk Levels

- **Low**: High hit rates (85%+), conservative odds, 2-4 legs
- **Medium**: Balanced approach (75%+), moderate risk, 3-6 legs
- **High**: Aggressive strategy (60%+), higher payouts, 5+ legs

## How It Works

1. **Data Fetching**: Retrieves recent player game logs from SportsDataIO
2. **Hit Rate Calculation**: Analyzes last 10-20 games to calculate prop hit rates
3. **Odds Estimation**: Uses historical trends to estimate fair odds for each prop
4. **Optimization**: Finds best combination of props to meet target criteria
5. **Confidence Scoring**: Calculates overall parlay confidence based on multiple factors

## Example Use Cases

### Conservative $100 Parlay
```bash
curl -X POST "http://localhost:8002/api/v1/generate-tier-parlay" \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "$100",
    "sport": "mlb", 
    "max_legs": 4,
    "min_hit_rate": 0.9
  }'
```

### Aggressive +5000 Odds Target
```bash
curl -X POST "http://localhost:8002/api/v1/generate-custom-parlay" \
  -H "Content-Type: application/json" \
  -d '{
    "target_odds": 5000,
    "risk_level": "high",
    "sport": "nfl",
    "max_legs": 10,
    "min_hit_rate": 0.6
  }'
```

## API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## Architecture

```
/parlay-optimizer/
├── main.py                    # FastAPI application
├── /routes
│   ├── generate_parlay_tier.py    # Tier-based parlay endpoint
│   └── generate_parlay_custom.py  # Custom odds parlay endpoint
├── /services
│   └── sportsdata_io.py           # SportsDataIO API integration
├── /utils
│   └── odds_math.py               # Odds calculations and parlay math
├── /models
│   └── parlay_schema.py           # Pydantic models and schemas
├── .env                           # Environment configuration
└── requirements.txt               # Python dependencies
```

## Development

### Running Tests
```bash
python test_optimizer.py
```

### Adding New Sports
1. Add sport to `SportType` enum in `models/parlay_schema.py`
2. Add prop types to `PropType` enum
3. Implement sport-specific hit rate calculations in `services/sportsdata_io.py`
4. Add odds estimation logic in `utils/odds_math.py`

### Custom Prop Types
1. Define new prop type in `PropType` enum
2. Add default line value in `_get_default_line()` functions
3. Add odds estimation in `estimate_prop_odds()`
4. Implement hit rate calculation logic

## License

MIT License - See LICENSE file for details
