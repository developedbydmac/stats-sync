# 📋 Tomorrow's Integration Tasks

## Priority 1: Real API Key Setup

### Step 1: Get SportsDataIO API Key
- [ ] Sign up at https://sportsdata.io
- [ ] Choose appropriate subscription plan (start with free tier)
- [ ] Note rate limits and endpoint access

### Step 2: Environment Configuration
```bash
# Create/update .env file
echo "SPORTSDATAIO_API_KEY=your_actual_api_key_here" >> .env
```

### Step 3: Test API Connectivity
```bash
# Run integration test
python -c "import asyncio; from tests.test_real_api_integration import manual_api_test; asyncio.run(manual_api_test())"
```

## Priority 2: API Response Mapping

### Current Issues to Fix:
1. **Endpoint URLs** - Verify correct SportsDataIO API endpoints
2. **Response Structure** - Map API response to our PlayerProp model
3. **Prop Types** - Ensure PropType enum matches API prop categories
4. **Odds Format** - Handle different odds formats (American/Decimal)

### Files to Update:
- `src/services/sports_data_service.py`:
  - Update `_get_props_endpoint()` with correct URLs
  - Implement `_transform_api_response()` method
  - Add error handling for different response formats

### API Response Structure Research:
```python
# Expected SportsDataIO response format (verify with actual API):
{
    "GameID": 12345,
    "PlayerID": 67890,
    "Name": "Aaron Judge",
    "Team": "NYY",
    "Opponent": "BOS",
    "PlayerProps": [
        {
            "PropType": "HomeRuns",
            "Line": 0.5,
            "OverOdds": 180,
            "UnderOdds": -220
        }
    ]
}
```

## Priority 3: Data Validation

### Test Scenarios:
- [ ] Fetch props for current MLB games
- [ ] Validate data types match our models
- [ ] Test error handling (bad API key, network issues)
- [ ] Verify confidence calculation with real hit rates
- [ ] Test parlay generation with live data

### Validation Checklist:
```python
# Ensure these fields exist in API response:
required_fields = [
    'player_name',  # Player name
    'team',         # Player's team
    'opponent',     # Opposing team  
    'prop_type',    # Type of prop (hits, home_runs, etc.)
    'line',         # Over/under line
    'over_odds',    # Odds for over
    'under_odds'    # Odds for under
]
```

## Priority 4: Historical Data Integration

### Current State:
- Mock historical data: 600 enhanced records
- Hit rates: Realistic (50-65% range)
- Confidence engine: Working with mock data

### Integration Steps:
1. **Collect Real Historical Data**
   - Use SportsDataIO historical endpoints
   - Gather last 30 days of prop results
   - Store in same CSV format as mock data

2. **Update PropAnalyzer**
   - Replace mock data with real historical results
   - Validate confidence calculations
   - Adjust confidence thresholds if needed

## Priority 5: Error Handling & Monitoring

### Add Production-Ready Features:
- [ ] Rate limit handling (respect API quotas)
- [ ] Retry logic for failed requests
- [ ] Logging for API calls and errors
- [ ] Health check endpoint for API status
- [ ] Fallback to mock data on API failures

### Monitoring Setup:
```python
# Add to sports_data_service.py:
- API call success/failure rates
- Response time tracking
- Quota usage monitoring
- Error categorization (network, auth, rate limit)
```

## Quick Test Commands

### After API Key Setup:
```bash
# Test server restart
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Test parlay generation with real data
curl "http://localhost:8001/parlays?sport=MLB&tier=Premium&count=3"

# Check system stats
curl "http://localhost:8001/stats" | python3 -m json.tool

# Run integration tests
python -m pytest tests/test_real_api_integration.py -v
```

### Verification Points:
- [ ] Confidence scores vary realistically (not all 100%)
- [ ] Player names match current rosters
- [ ] Prop lines reflect actual sportsbook lines
- [ ] Parlays generate successfully
- [ ] System falls back to mock data on API errors

## Expected Outcomes

### Success Criteria:
1. **Real Data Flow**: Live props from SportsDataIO displaying in parlays
2. **Realistic Confidence**: Scores vary based on actual performance
3. **Error Resilience**: System works even with API issues
4. **Performance**: Response times under 2 seconds
5. **Accuracy**: Prop data matches what you'd see on actual sportsbooks

### Next Phase (After Integration):
- Multi-sportsbook odds comparison
- Real-time line movement tracking
- Enhanced injury/weather data
- Machine learning model improvements
- User feedback integration

---

## 🚨 Critical Notes

1. **Mock Data Backup**: Keep mock data system - it's your safety net
2. **Rate Limits**: Monitor API usage to avoid service interruption
3. **Data Quality**: Validate all incoming data before use
4. **Error Logging**: Track all API failures for debugging
5. **Gradual Rollout**: Test thoroughly before full deployment

**File References:**
- Main integration plan: `INTEGRATION_PLAN.md`
- Test file: `tests/test_real_api_integration.py`
- Service file: `src/services/sports_data_service.py`
- Environment template: `.env.example`
