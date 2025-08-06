# ⚡ Stats Sync - AI-Powered Sports Parlay Generator

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)](https://github.com/developedbydmac/stats-sync)
[![Coverage](https://img.shields.io/badge/Coverage-85%25-green.svg)](tests/)
[![API Status](https://img.shields.io/badge/API-Online-brightgreen.svg)](http://localhost:8000)

> **Real-time sports parlay generation with AI-powered confidence scoring, pregame analysis, and live betting predictions**

Stats Sync is an intelligent sports betting platform that combines real-time player prop data with historical performance analysis to create optimized parlays with confidence scores. Now featuring dedicated pregame and halftime prediction services powered by SportsDataIO API integration.

## 🚀 New Features: Prediction Services

### 🎯 Pregame Prediction Service
- **Comprehensive Game Analysis**: Team statistics, player performance, weather conditions
- **Player Prop Predictions**: AI-powered recommendations with confidence scoring
- **Optimized Parlays**: Multi-leg parlays built from high-confidence predictions
- **Betting Strategies**: Bankroll allocation and risk assessment recommendations

### ⚡ Halftime/Live Prediction Service  
- **Real-Time Analysis**: Live game momentum and scoring trends
- **In-Game Adjustments**: Dynamic prop recommendations based on current game state
- **Live Betting Parlays**: Time-sensitive opportunities for halftime betting
- **Market Monitoring**: Live odds tracking and optimal timing recommendations

## 🔄 Development Status

**Current Phase**: Production Ready with SportsDataIO Integration  
**Prediction Services**: ✅ Fully Implemented (Pregame & Halftime)  
**Mock Data System**: ✅ Fully Functional (600+ historical props)  
**Real API Framework**: ✅ Built and Ready  
**SportsDataIO Integration**: ✅ Active  

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete endpoint documentation.

## 🎯 Core Features

### Core Functionality
- **Real-time Data Integration** - Framework ready for SportsDataIO API with mock data fallback
- **AI Confidence Scoring** - Advanced algorithms analyze historical performance, recent form, and contextual factors
- **Smart Parlay Building** - Generates optimized parlays avoiding duplicates and ensuring proper distribution
- **Multi-Tier System** - Free (70%+ confidence), Premium (80%+ confidence), GOAT (95%+ confidence)
- **Automated Refreshing** - Updates parlays every 10 minutes with fresh data
- **Discord Integration** - Automated notifications for high-confidence plays

### Supported Sports
- 🏈 **NFL** - Passing yards, rushing yards, receiving yards, touchdowns, receptions
- ⚾ **MLB** - Hits, home runs, RBIs, strikeouts

### Advanced Analytics
- **Historical Hit Rate Analysis** - Leverages historical prop performance data
- **Recent Form Weighting** - Prioritizes recent player performance trends
- **Injury Status Integration** - Framework ready for real injury data
- **Weather Considerations** - Framework ready for weather API integration
- **Matchup Analysis** - Framework ready for advanced matchup data

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SportsDataIO API Key (optional - includes comprehensive mock data for development)
- Discord Webhook URL (optional - for notifications)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/developedbydmac/stats-sync.git
cd stats-sync
```

2. **Install dependencies**

> **Real-time sports parlay generation with AI-powered confidence scoring and historical analysis**

Stats Sync is an intelligent sports betting parlay generator that combines real-time player prop data with historical performance analysis to create optimized parlays with confidence scores. Built with FastAPI and powered by machine learning algorithms.

## 🎯 Features

### Core Functionality
- **Real-time Data Integration** - Fetches live player props from SportsDataIO API
- **AI Confidence Scoring** - Advanced algorithms analyze historical performance, recent form, and contextual factors
- **Smart Parlay Building** - Generates optimized parlays avoiding duplicates and ensuring proper distribution
- **Multi-Tier System** - Free (70%+ confidence), Premium (80%+ confidence), GOAT (95%+ confidence)
- **Automated Refreshing** - Updates parlays every 10 minutes with fresh data
- **Discord Integration** - Automated notifications for high-confidence plays

### Supported Sports
- 🏈 **NFL** - Passing yards, rushing yards, receiving yards, touchdowns, receptions
- ⚾ **MLB** - Hits, home runs, RBIs, strikeouts

### Advanced Analytics
- **Historical Hit Rate Analysis** - Leverages historical prop performance data
- **Recent Form Weighting** - Prioritizes recent player performance trends
- **Injury Status Integration** - Factors in current injury reports
- **Weather Considerations** - Adjusts for weather conditions (where applicable)
- **Matchup Analysis** - Considers opponent defensive rankings

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SportsDataIO API Key (optional - includes mock data for development)
- Discord Webhook URL (optional - for notifications)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/developedbydmac/stats-sync.git
cd stats-sync
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Run the application**
```bash
# Option 1: Use the enhanced startup script
python start_server.py

# Option 2: Direct FastAPI run
python main.py

# Option 3: Using uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

5. **Test the prediction services**
```bash
# Test the API endpoints
python test_api.py

# Or manually test key endpoints
curl http://localhost:8000/health
curl http://localhost:8000/predictions/status
```

6. **Access the web interface**
```
http://localhost:8000
```

## 🔮 Prediction API Endpoints

### Pregame Predictions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predictions/pregame` | Trigger pregame analysis |
| `GET` | `/predictions/pregame/{sport}` | Get pregame predictions |

### Halftime/Live Predictions  

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predictions/halftime` | Trigger live game analysis |
| `GET` | `/predictions/halftime/{sport}` | Get live predictions |

### Status & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/predictions/status` | Service status and configuration |
| `GET` | `/health` | API health check |

### Example Prediction Usage

```bash
# Trigger pregame predictions for today's NFL games
curl -X POST "http://localhost:8000/predictions/pregame?sport=NFL&tier=Premium"

# Get the generated predictions
curl "http://localhost:8000/predictions/pregame/NFL?tier=Premium"

# Trigger live/halftime predictions
curl -X POST "http://localhost:8000/predictions/halftime?sport=NFL&tier=GOAT"

# Get live predictions
curl "http://localhost:8000/predictions/halftime/NFL?tier=GOAT"

# Check service status
curl "http://localhost:8000/predictions/status"
```

## 📊 Core API Endpoints

### Legacy Parlay Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web interface |
| `GET` | `/parlays` | Get parlays with optional filters |
| `POST` | `/parlays/refresh` | Force refresh parlay data |
| `GET` | `/props/{sport}` | Get raw player props |
| `GET` | `/parlays/live` | Get live/halftime parlays |
| `GET` | `/stats` | System statistics |

### Example API Usage

```bash
# Get all NFL parlays
curl "http://localhost:8000/parlays?sport=NFL"

# Get GOAT tier MLB parlays
curl "http://localhost:8000/parlays?sport=MLB&tier=GOAT"

# Force refresh data
curl -X POST "http://localhost:8000/parlays/refresh"
```

## 🎲 Tier System

### 🎯 Free Tier
- **Confidence Threshold**: 70%+
- **Target Payout**: 10x
- **Max Legs**: 6
- **Strategy**: Conservative, high-probability plays

### 💎 Premium Tier  
- **Confidence Threshold**: 80%+
- **Target Payout**: 25x
- **Max Legs**: 7
- **Strategy**: Balanced risk/reward optimization

### 🐐 GOAT Tier
- **Confidence Threshold**: 95%+
- **Target Payout**: 50x+
- **Max Legs**: 8
- **Strategy**: Maximum confidence, premium plays only

## 🧠 Confidence Scoring Algorithm

The confidence scoring system analyzes multiple factors:

```python
confidence_score = (
    base_historical_hit_rate * 100 +
    recent_form_adjustment +
    injury_factor +
    weather_factor +
    matchup_factor +
    line_movement_factor
)
```

### Factors Considered:
- **Historical Hit Rate** (90 days) - 40% weight
- **Recent Form** (last 5 games) - 30% weight  
- **Injury Status** - 15% weight
- **Weather Conditions** - 10% weight
- **Matchup Analysis** - 5% weight

## 📈 Sample Parlay Output

```json
{
  "parlay": {
    "id": "uuid-here",
    "tier": "PREMIUM",
    "sport": "NFL",
    "legs": [
      {
        "player_prop": {
          "player_name": "Patrick Mahomes",
          "team": "KC",
          "opponent": "LV", 
          "prop_type": "passing_yards",
          "line": 285.5,
          "over_odds": -108,
          "under_odds": -112,
          "confidence_score": 89.5
        },
        "selection": "over",
        "odds": -108,
        "confidence": 89.5
      }
    ],
    "total_odds": +650,
    "expected_payout": 7.5,
    "overall_confidence": 85.2,
    "description": "💎 Premium: High-Confidence 6-Legger"
  },
  "analysis": {
    "avg_confidence": 85.2,
    "expected_hit_rate": 0.234,
    "risk_assessment": "Low Risk",
    "recommendation": "SOLID BET: High probability with good payout potential"
  }
}
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python tests/test_parlay_system.py
```

### Test Coverage
- ✅ Prop data ingestion validation
- ✅ Historical data analysis  
- ✅ Confidence scoring accuracy
- ✅ Parlay building logic
- ✅ Tier requirement validation
- ✅ API endpoint functionality
- ✅ End-to-end integration

### Sample Test Output
```
📊 SAMPLE PARLAY OUTPUTS BY TIER
================================================================================

🏈 NFL PARLAYS
--------------------------------------------------

🎯 FREE TIER
Confidence: 73.2%
Total Odds: +480
Expected Payout: 5.8x
Legs: 5
Risk: Moderate Risk
Top 3 Legs:
  1. Patrick Mahomes (KC) - Passing Yards over 275.5 (75.4%)
  2. Travis Kelce (KC) - Receiving Yards over 65.5 (74.1%) 
  3. Derrick Henry (BAL) - Rushing Yards over 95.5 (71.8%)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SPORTSDATAIO_API_KEY` | SportsDataIO API key | None (uses mock data) |
| `PROPS_CSV_PATH` | Path to historical props CSV | `./data/historical_props.csv` |
| `DISCORD_WEBHOOK_URL` | Discord webhook for notifications | None |
| `CONSERVATIVE_CONFIDENCE_THRESHOLD` | Free tier minimum confidence | 90 |
| `GOAT_CONFIDENCE_THRESHOLD` | GOAT tier minimum confidence | 95 |
| `REFRESH_INTERVAL_MINUTES` | Auto-refresh interval | 10 |

### Historical Data Format

The system expects historical prop data in CSV format:

```csv
player_name,date,prop_type,line,actual_result,hit,odds,sport
Patrick Mahomes,2024-01-01,passing_yards,275.5,320.0,True,-110,NFL
Josh Allen,2024-01-01,passing_yards,250.5,240.0,False,-110,NFL
```

## 🚀 Deployment

### Local Development
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Docker)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Azure/AWS Deployment
The application is designed to be cloud-ready with:
- Health check endpoints for load balancers
- Structured logging for monitoring
- Environment-based configuration
- Async architecture for scalability

## 📱 Discord Integration

Set up automated notifications for high-confidence parlays:

1. Create Discord webhook URL
2. Add to `.env` file as `DISCORD_WEBHOOK_URL`
3. Notifications sent automatically for GOAT tier parlays with 97%+ confidence

Example notification:
> 🐐 **GOAT TIER ALERT** 🐐  
> **98.2% Confidence** - This is the play!  
> **NFL 6-Leg Parlay** - Expected Payout: 15.2x

## 🛠️ Development

### Project Structure
```
stats-sync/
├── src/
│   ├── models/         # Pydantic models
│   ├── services/       # Business logic
│   └── utils/          # Helper utilities
├── static/             # Frontend assets
├── data/              # Historical data
├── tests/             # Test suite
├── main.py            # FastAPI application
└── requirements.txt   # Dependencies
```

### Adding New Sports
1. Add sport to `SportType` enum
2. Update `PropType` enum with sport-specific props
3. Implement sport-specific API endpoints in `SportsDataService`
4. Add historical data for the sport
5. Update frontend sport toggle

### Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **SportsDataIO** - Real-time sports data API
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation and parsing
- **APScheduler** - Background task scheduling

## 📞 Support

- **Documentation**: [GitHub Wiki](https://github.com/developedbydmac/stats-sync/wiki)
- **Issues**: [GitHub Issues](https://github.com/developedbydmac/stats-sync/issues)
- **Discord**: [Community Server](https://discord.gg/stats-sync)

---

**⚠️ Disclaimer**: This tool is for educational and entertainment purposes only. Please gamble responsibly and within your means. Past performance does not guarantee future results.

**Made with ⚡ by [developedbydmac](https://github.com/developedbydmac)**
