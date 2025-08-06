# Stats Sync API Documentation

## Overview

The Stats Sync API is a FastAPI application that loads environment variables from a `.env` file for the SportsDataIO API key and provides endpoints to trigger pregame and halftime prediction scripts.

## Environment Setup

### Required Environment Variables

Create a `.env` file in the root directory with the following variables:

```properties
# API Keys
SPORTSDATA_API_KEY=your_sportsdata_api_key_here

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Parlay Configuration
CONSERVATIVE_CONFIDENCE_THRESHOLD=90
GOAT_CONFIDENCE_THRESHOLD=95
MIN_PARLAY_LEGS=5
MAX_PARLAY_LEGS=8
REFRESH_INTERVAL_MINUTES=10

# API Endpoints
SPORTSDATAIO_BASE_URL=https://api.sportsdata.io/v3
```

### SportsDataIO API Key

Get your API key from [SportsDataIO](https://sportsdata.io/) and replace `your_sportsdata_api_key_here` with your actual key.

## Starting the Application

### Option 1: Using the Startup Script
```bash
python start_server.py
```

### Option 2: Direct FastAPI Run
```bash
python main.py
```

### Option 3: Using Uvicorn
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Health & Status

#### GET /health
Health check endpoint to verify the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "stats-sync-api"
}
```

#### GET /predictions/status
Get the status of prediction services and configuration.

**Response:**
```json
{
  "pregame_service": "initialized",
  "halftime_service": "initialized",
  "sportsdata_api_configured": true,
  "api_key_partial": "b6d30590...",
  "supported_sports": ["NFL", "MLB", "NBA", "NHL"],
  "supported_tiers": ["Free", "Premium", "GOAT"],
  "timestamp": "2025-01-08T10:30:00Z"
}
```

### Pregame Predictions

#### POST /predictions/pregame
Trigger the pregame prediction script for a specific sport and date.

**Parameters:**
- `sport` (required): Sport type (NFL, MLB, NBA, NHL)
- `date` (optional): Game date in YYYY-MM-DD format (defaults to today)
- `tier` (optional): Tier level for filtering parlays (Free, Premium, GOAT)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/predictions/pregame?sport=NFL&date=2025-01-08&tier=Premium"
```

**Response:**
```json
{
  "message": "Pregame prediction script triggered for NFL",
  "sport": "NFL",
  "date": "2025-01-08",
  "tier": "Premium",
  "status": "processing"
}
```

#### GET /predictions/pregame/{sport}
Get pregame predictions for a specific sport and date.

**Parameters:**
- `sport` (path, required): Sport type (NFL, MLB, NBA, NHL)
- `date` (query, optional): Game date in YYYY-MM-DD format
- `tier` (query, optional): Tier level for filtering parlays

**Example Request:**
```bash
curl "http://localhost:8000/predictions/pregame/NFL?date=2025-01-08&tier=Premium"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "predictions": {
      "games": [...],
      "player_props": [...]
    },
    "parlays": [...],
    "analysis": {
      "sport": "NFL",
      "date": "2025-01-08",
      "total_games": 16,
      "total_props": 250,
      "high_confidence_props": 45,
      "generated_parlays": 8
    },
    "recommendations": {...}
  },
  "metadata": {
    "sport": "NFL",
    "date": "2025-01-08",
    "tier": "Premium",
    "generated_at": "2025-01-08T10:30:00Z"
  }
}
```

### Halftime/Live Predictions

#### POST /predictions/halftime
Trigger the halftime prediction script for live games.

**Parameters:**
- `sport` (required): Sport type (NFL, MLB, NBA, NHL)
- `game_id` (optional): Specific game ID (analyzes all live games if not provided)
- `tier` (optional): Tier level for filtering parlays

**Example Request:**
```bash
curl -X POST "http://localhost:8000/predictions/halftime?sport=NFL&game_id=12345&tier=GOAT"
```

**Response:**
```json
{
  "message": "Halftime prediction script triggered for NFL",
  "sport": "NFL",
  "game_id": "12345",
  "tier": "GOAT",
  "status": "processing"
}
```

#### GET /predictions/halftime/{sport}
Get halftime/live predictions for a specific sport.

**Parameters:**
- `sport` (path, required): Sport type (NFL, MLB, NBA, NHL)
- `game_id` (query, optional): Specific game ID
- `tier` (query, optional): Tier level for filtering parlays

**Example Request:**
```bash
curl "http://localhost:8000/predictions/halftime/NFL?game_id=12345&tier=GOAT"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "predictions": {
      "games": [...],
      "live_props": [...]
    },
    "parlays": [...],
    "analysis": {
      "sport": "NFL",
      "live_games": 8,
      "live_props": 150,
      "high_confidence_plays": 25,
      "generated_parlays": 6,
      "market_conditions": {...}
    },
    "recommendations": {...}
  },
  "metadata": {
    "sport": "NFL",
    "game_id": "12345",
    "tier": "GOAT",
    "generated_at": "2025-01-08T15:30:00Z"
  }
}
```

### Legacy Endpoints (Existing Functionality)

#### GET /parlays
Get parlays for a specific sport and tier.

**Parameters:**
- `sport` (optional): Sport type (default: NFL)
- `tier` (optional): Tier filter
- `refresh` (optional): Force refresh of data

#### POST /parlays/refresh
Manually trigger parlay refresh.

#### GET /props/{sport}
Get real-time player props for a sport.

#### GET /parlays/live
Get live/halftime parlays for in-game betting.

#### GET /stats
Get system statistics.

## Supported Sports

- **NFL**: National Football League
- **MLB**: Major League Baseball  
- **NBA**: National Basketball Association
- **NHL**: National Hockey League

## Supported Tiers

- **Free**: Basic predictions with standard confidence thresholds
- **Premium**: Enhanced predictions with higher confidence requirements
- **GOAT**: Elite predictions with the highest confidence thresholds

## Error Handling

All endpoints return standardized error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200`: Success
- `500`: Internal server error
- `422`: Validation error (invalid parameters)

## Prediction Services

### Pregame Prediction Service

The pregame prediction service analyzes:
- Scheduled games for the specified date
- Player props and historical performance
- Team statistics and trends
- Weather conditions and other factors

Generates:
- Game outcome predictions
- Player prop recommendations
- Optimized parlays
- Betting strategies

### Halftime Prediction Service

The halftime prediction service analyzes:
- Live game states and momentum
- Real-time player performance
- In-game trends and patterns
- Live betting odds

Generates:
- Live game predictions
- Halftime prop adjustments
- Live betting parlays
- Time-sensitive recommendations

## Integration

The API integrates with:
- **SportsDataIO**: Primary sports data provider
- **OddsJam**: Live odds and prop data
- **Internal Services**: Parlay building and optimization

## Development

### Project Structure
```
stats-sync/
├── main.py                    # FastAPI application
├── start_server.py           # Startup script
├── .env                      # Environment variables
├── src/
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   │   ├── pregame_prediction_service.py
│   │   ├── halftime_prediction_service.py
│   │   └── ...
│   └── utils/               # Utilities
└── requirements.txt         # Dependencies
```

### Running in Development Mode

1. Set `DEBUG=True` in your `.env` file
2. Start the server: `python start_server.py`
3. The API will automatically reload on code changes

### Testing

Use curl, Postman, or any HTTP client to test the endpoints:

```bash
# Test health
curl http://localhost:8000/health

# Test status
curl http://localhost:8000/predictions/status

# Trigger pregame predictions
curl -X POST "http://localhost:8000/predictions/pregame?sport=NFL"

# Get pregame predictions
curl "http://localhost:8000/predictions/pregame/NFL"
```

## Logging

The application uses structured logging with the following levels:
- `INFO`: General application flow
- `WARNING`: Potential issues or missing data
- `ERROR`: Error conditions that need attention

Logs include timestamps, service names, and contextual information for debugging.

## Support

For issues or questions:
1. Check the application logs for error details
2. Verify your SportsDataIO API key is valid and has sufficient quota
3. Ensure all required environment variables are set
4. Check that the sports and dates you're requesting are supported
