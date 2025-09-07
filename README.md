# 🎯 Vinted Monitor - AI-Powered & Stealth

**The most advanced Vinted scraper with AI analysis, anti-detection, and market tracking.**

## ✨ Features

- 🤖 **AI-Powered Analysis**: OpenAI/Anthropic/Gemini integration for precise product matching
- 🛡️ **Anti-Detection**: Advanced stealth measures to avoid bot detection
- 📊 **Market Tracking**: Google Sheets integration for real-time market trends
- 🔔 **Smart Notifications**: Discord alerts only for relevant matches
- 🌍 **Multi-Domain**: Supports all Vinted domains (FR, DE, IT, ES, etc.)
- 💱 **Currency Conversion**: Cross-domain price comparison
- 🗄️ **Deduplication**: Never get the same notification twice

## 🚀 Quick Start

### 1. Installation

```bash
# Clone and setup
git clone <repository-url>
cd vinted-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Configuration

```bash
# Copy configuration templates
cp .env.example .env
cp config/watches.yaml.example config/watches.yaml

# Edit .env with your API keys
nano .env
```

**Required in `.env`:**
- `DISCORD_WEBHOOK_URL` - Your Discord webhook
- `OPENAI_API_KEY` - OpenAI API key for AI analysis

**Optional in `.env`:**
- `GOOGLE_CREDENTIALS_PATH` - For market tracking sheets
- `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` - Alternative AI providers

### 3. Setup Watches

Edit `config/watches.yaml`:

```yaml
watches:
  - name: "Nike Air Force 1"
    vinted_domain: "vinted.fr"
    query: "nike air force 1"
    max_price: 80.0
    currency: "EUR"
    polling_interval_sec: 45
    filters:
      order: "newest_first"
      price_from: 30.0
    min_seller_rating: 4.0
    min_seller_feedback_count: 5
```

### 4. Launch

```bash
# Test your configuration
python -m app.main test-watch "Nike Air Force 1" --dry-run

# Start monitoring
python -m app.main run
```

## 🤖 AI Analysis

The AI system analyzes each listing to determine if it truly matches your requirements:

- **Product Matching**: Ensures listings match exactly what you're looking for
- **Price Analysis**: Evaluates if the price is reasonable for the item
- **Quality Assessment**: Rates deal quality (excellent/good/fair/poor)
- **Market Comparison**: Compares against historical market data

### AI Providers

| Provider | Cost | Speed | Accuracy | Setup |
|----------|------|-------|----------|-------|
| **OpenAI** | Low | Fast | Excellent | Easy |
| **Anthropic** | Medium | Fast | Excellent | Easy |
| **Gemini** | Free* | Medium | Good | Easy |

*Gemini has free tier available

## 📊 Market Tracking

Enable Google Sheets integration to track market trends:

1. **Create Google Service Account**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project → Enable Sheets API
   - Create Service Account → Download JSON credentials
   - Save as `credentials.json`

2. **Automatic Tracking**:
   - All listings logged to sheets
   - Market trends calculated hourly
   - Price history and analysis
   - Deal recommendations

## 🛡️ Anti-Detection Features

- **Randomized Delays**: 1200-2500ms between requests
- **Browser Fingerprinting**: Realistic browser signatures
- **Request Patterns**: Human-like browsing behavior
- **Rate Limiting**: Respects Vinted's servers
- **Cookie Management**: Handles consent popups automatically

## 📱 Commands

```bash
# Core commands
python -m app.main run                    # Start monitoring
python -m app.main status                 # Show status
python -m app.main list-watches           # List all watches

# Testing
python -m app.main test-watch "Name"      # Test with notifications
python -m app.main test-watch "Name" --dry-run  # Test without notifications
python -m app.main test-webhook           # Test Discord webhook
python -m app.main test-domain vinted.fr  # Test domain access

# Management
python -m app.main clear-seen "Name"      # Clear seen listings
python -m app.main cleanup --days 30      # Clean old data
```

## ⚙️ Configuration Guide

### Watch Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `name` | ✅ | Unique watch name | "Nike Air Force 1" |
| `vinted_domain` | ✅ | Vinted domain | "vinted.fr" |
| `query` | ✅ | Search query | "nike air force 1" |
| `max_price` | ✅ | Maximum price | 80.0 |
| `currency` | ❌ | Currency code | "EUR" |
| `polling_interval_sec` | ❌ | Check interval | 45 |
| `min_seller_rating` | ❌ | Min seller rating | 4.0 |
| `min_seller_feedback_count` | ❌ | Min feedback count | 5 |

### Advanced Filters

```yaml
filters:
  order: "newest_first"        # Sort order
  price_from: 30.0            # Minimum price
  category_ids: [1234]        # Category filters
  brand_ids: [5678]           # Brand filters
  size_ids: [42, 43]          # Size filters
  condition_ids: [1, 2]       # Condition filters
```

### Performance Tuning

```env
# Conservative (stable)
DEFAULT_POLL_INTERVAL_SEC=60
CONCURRENCY=1
MAX_PAGES_PER_POLL=1

# Balanced (recommended)
DEFAULT_POLL_INTERVAL_SEC=45
CONCURRENCY=1
MAX_PAGES_PER_POLL=2

# Aggressive (higher detection risk)
DEFAULT_POLL_INTERVAL_SEC=30
CONCURRENCY=2
MAX_PAGES_PER_POLL=3
```

## 🔧 Troubleshooting

### Common Issues

**1. "No module named 'openai'"**
```bash
pip install -r requirements.txt
```

**2. "Browser launch failed"**
```bash
playwright install chromium
playwright install-deps chromium
```

**3. "AI analysis failed"**
- Check your API key in `.env`
- Verify API key has credits/quota
- Try different AI provider

**4. "No listings found"**
```bash
# Test domain access
python -m app.main test-domain vinted.fr

# Test specific watch
python -m app.main test-watch "Your Watch" --dry-run
```

**5. "Discord webhook failed"**
```bash
# Test webhook
python -m app.main test-webhook
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m app.main run
```

## 📈 Performance Stats

The system tracks detailed statistics:

- **Listings Found**: Total listings discovered
- **AI Analysis**: Matches vs rejects with confidence scores
- **Notifications**: Successful Discord notifications sent
- **Market Data**: Listings logged to Google Sheets
- **Success Rate**: Overall system performance

View stats: `python -m app.main status`

## 🌍 Supported Domains

| Domain | Country | Currency | Status |
|--------|---------|----------|--------|
| vinted.fr | France | EUR | ✅ |
| vinted.com | USA | USD | ✅ |
| vinted.de | Germany | EUR | ✅ |
| vinted.it | Italy | EUR | ✅ |
| vinted.es | Spain | EUR | ✅ |
| vinted.pl | Poland | PLN | ✅ |
| vinted.lt | Lithuania | EUR | ✅ |
| vinted.cz | Czech Republic | CZK | ✅ |

## 🔒 Security & Ethics

### Best Practices

- ✅ **Reasonable Intervals**: Minimum 45 seconds between polls
- ✅ **Limited Concurrency**: Max 1-2 concurrent requests
- ✅ **Respectful Usage**: Don't overload Vinted's servers
- ✅ **Personal Use**: For personal monitoring only
- ✅ **Data Privacy**: No sharing of scraped data

### Legal Compliance

This tool is for **educational and personal use only**. Users are responsible for:
- Complying with Vinted's Terms of Service
- Respecting rate limits and server resources
- Not using for commercial purposes
- Following applicable laws in their jurisdiction

## 🚀 Advanced Usage

### Docker Deployment

```bash
# Build and run with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Multiple AI Providers

```env
# Fallback chain: OpenAI → Anthropic → Gemini
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
AI_PROVIDER=openai
```

### Custom Market Analysis

```python
# Access market data programmatically
from app.sheets_integration import create_sheets_manager

sheets = await create_sheets_manager()
market_data = await sheets.get_market_data("Nike Air Force 1", days=30)
print(f"Average price: {market_data['avg_price']}")
```

## 📊 Project Structure

```
vinted-monitor/
├── app/
│   ├── ai_analyzer.py       # AI analysis engine
│   ├── sheets_integration.py # Google Sheets tracking
│   ├── scheduler.py         # Optimized scheduler
│   ├── scraper/            # Web scraping
│   ├── notifier/           # Discord notifications
│   └── ...
├── config/
│   └── watches.yaml        # Watch configurations
├── .env                    # Environment variables
└── requirements.txt        # Dependencies
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Playwright** - Web automation framework
- **OpenAI/Anthropic/Google** - AI analysis providers
- **Discord** - Notification platform
- **Google Sheets** - Market data tracking

---

**⚡ Ready to find the best deals on Vinted with AI precision? Get started now!**
