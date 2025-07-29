# Real Sports Data API Integration Plan

## Overview
This document outlines the integration plan for connecting the Stats Sync parlay generator to real sports data APIs. The system is currently built with a comprehensive mock data framework that will be replaced with live data sources.

## Current Architecture Status

### ✅ Already Implemented
- **Mock Data System**: Fully functional fallback with 600 historical prop records
- **API Service Layer**: `SportsDataService` class with async HTTP client
- **Data Models**: Complete Pydantic models for props, parlays, and analytics
- **Confidence Engine**: `PropAnalyzer` with historical performance tracking
- **Caching System**: In-memory cache with automatic refresh cycles
- **Environment Configuration**: `.env` setup for API keys

### 🔄 Ready for Integration
- **API Key Detection**: System automatically switches between mock and live data
- **Error Handling**: Graceful fallback to mock data on API failures
- **Rate Limiting**: Built-in request throttling and retry logic

## API Integration Strategy

### Primary Data Sources

#### 1. SportsDataIO (Main Provider)
- **Current Setup**: Framework implemented in `src/services/sports_data_service.py`
- **API Key**: `SPORTSDATAIO_API_KEY` environment variable
- **Coverage**: MLB, NFL player props and odds
- **Endpoints**:
  - Player Props: `/mlb/odds/{date}/playerprops`
  - Team Stats: `/mlb/teams/{season}/stats`
  - Player Stats: `/mlb/players/{season}/stats`
  - Injuries: `/mlb/injuries`

#### 2. Secondary APIs (Backup/Enhancement)
- **The Odds API**: For odds comparison and line movement
- **ESPN API**: For player news and injury updates  
- **Baseball Reference/Pro Football Reference**: Historical performance data

### Implementation Phases

#### Phase 1: SportsDataIO Integration (Tomorrow's Work)

**Step 1: API Key Setup**
```bash
# Create .env file with real API key
echo "SPORTSDATAIO_API_KEY=your_real_api_key_here" > .env
```

**Step 2: Enable Live Data Fetching**
- Update `fetch_player_props()` method in `SportsDataService`
- Test API connectivity and response parsing
- Validate data mapping to our `PlayerProp` model

**Step 3: Prop Data Mapping**
```python
# Expected API response structure to map:
{
    "PlayerID": 12345,
    "Name": "Aaron Judge",
    "Team": "NYY",
    "Opponent": "BOS", 
    "HomeRuns": {
        "OverOdds": 180,
        "UnderOdds": -220,
        "Line": 0.5
    },
    "Hits": {
        "OverOdds": -110,
        "UnderOdds": -110, 
        "Line": 1.5
    }
}
```

**Step 4: Historical Data Enhancement**
- Replace mock historical data with real API data
- Implement 30-day rolling historical collection
- Update confidence scoring with real performance metrics

#### Phase 2: Advanced Features

**Multi-Source Data Aggregation**
- Compare odds across multiple sportsbooks
- Track line movement for better confidence scoring
- Real-time injury and weather data integration

**Enhanced Analytics**
- Player form tracking (last 10 games performance)
- Matchup analysis (pitcher vs batter historical data)
- Ballpark factors for MLB props

#### Phase 3: Production Optimization

**Caching Strategy**
- Redis integration for distributed caching
- Intelligent cache invalidation based on game times
- Pre-computed prop combinations for faster parlay generation

**Rate Limit Management**
- API quota monitoring and allocation
- Request prioritization (live games > future games)
- Fallback cascade (primary → secondary → mock data)

## Code Integration Points

### 1. Environment Variables (.env)
```bash
# Core API Keys
SPORTSDATAIO_API_KEY=your_sportsdataio_key
ODDS_API_KEY=your_odds_api_key
ESPN_API_KEY=your_espn_key

# API Configuration
SPORTSDATAIO_BASE_URL=https://api.sportsdata.io/v3
ODDS_API_BASE_URL=https://api.the-odds-api.com/v4
API_REQUEST_TIMEOUT=30
MAX_RETRIES=3

# Cache Settings
CACHE_DURATION_MINUTES=10
HISTORICAL_DATA_DAYS=30
```

### 2. Service Layer Updates

**SportsDataService Enhancement**
```python
async def fetch_live_player_props(self, sport: SportType, date: str = None) -> List[PlayerProp]:
    """Fetch real-time props with full error handling and fallback"""
    try:
        # Real API call
        props = await self._fetch_from_api(sport, date)
        # Validate and transform data
        return self._transform_api_response(props)
    except APIException as e:
        logger.warning(f"API failure, falling back to mock data: {e}")
        return self._generate_mock_props(sport, date)
```

**PropAnalyzer Enhancement**
```python
def calculate_confidence_with_live_data(self, prop: PlayerProp) -> float:
    """Enhanced confidence calculation using real historical data"""
    # Use actual 30-day performance data
    # Factor in real injury reports
    # Include weather conditions for outdoor sports
    # Apply sportsbook line movement analysis
```

### 3. Data Flow Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Request   │ -> │  SportsDataIO    │ -> │  Data Transform │
│   /parlays      │    │     Service      │    │   & Validation  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                 |                        |
                                 v                        v
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Mock Data     │ <- │  Error Handler   │    │  Prop Analyzer  │
│   Fallback      │    │   & Fallback     │    │  (Confidence)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         |
                                                         v
                                                ┌─────────────────┐
                                                │ Parlay Generator│
                                                │   & Response    │
                                                └─────────────────┘
```

## Testing Strategy

### API Integration Tests
```python
# Add to tests/test_sports_data_service.py
async def test_live_api_integration():
    """Test real API connectivity and data parsing"""
    service = SportsDataService()
    props = await service.fetch_player_props(SportType.MLB)
    assert len(props) > 0
    assert all(prop.confidence_score > 0 for prop in props)

async def test_api_fallback():
    """Test graceful fallback to mock data"""
    # Simulate API failure
    # Verify mock data is returned
    # Ensure service continues to function
```

### Load Testing
```python
# Test API rate limits and performance
async def test_concurrent_requests():
    """Ensure system handles multiple concurrent API calls"""
    tasks = [fetch_props_for_date(date) for date in date_range]
    results = await asyncio.gather(*tasks)
    # Validate all requests succeeded or failed gracefully
```

## Deployment Checklist

### Pre-Production
- [ ] API keys configured in environment
- [ ] Rate limit monitoring implemented  
- [ ] Error alerting setup (Discord webhook for API failures)
- [ ] Cache warming strategy for game days
- [ ] Backup data source configured

### Go-Live
- [ ] Monitor API quota usage
- [ ] Track confidence score accuracy vs actual results
- [ ] Performance metrics collection
- [ ] User feedback integration

## Tomorrow's Implementation Priority

1. **Set up real SportsDataIO API key** in `.env` file
2. **Test API connectivity** with live MLB data
3. **Implement prop data transformation** from API response to `PlayerProp` model
4. **Validate parlay generation** with real confidence scores
5. **Document API rate limits** and usage patterns
6. **Add error monitoring** for production readiness

## Long-term Enhancements

### Machine Learning Integration
- Player performance prediction models
- Injury impact analysis
- Weather correlation studies
- Optimal parlay combination algorithms

### Real-time Features
- Live odds tracking during games
- Push notifications for high-confidence parlays
- Dynamic parlay adjustment based on game events

### Business Intelligence
- User success rate tracking
- Tier upgrade conversion analytics
- Revenue optimization through prop selection

---

**Note**: The current system is fully functional with mock data. This plan ensures zero downtime during the transition to live data while maintaining all existing functionality.
