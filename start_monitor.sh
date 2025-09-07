#!/bin/bash

# =============================================================================
# VINTED MONITOR - OPTIMIZED STARTUP SCRIPT
# =============================================================================

set -e  # Exit on any error

echo "🚀 Starting Vinted Monitor - AI-Powered & Stealth"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "venv/pyvenv.cfg" ] || ! pip show playwright > /dev/null 2>&1; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    pip install -r requirements.txt
    playwright install chromium
fi

# Check configuration files
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚙️  Creating .env from template...${NC}"
    cp .env.example .env
    echo -e "${RED}❌ Please edit .env with your API keys and Discord webhook!${NC}"
    echo -e "${BLUE}   Required: DISCORD_WEBHOOK_URL, OPENAI_API_KEY${NC}"
    exit 1
fi

if [ ! -f "config/watches.yaml" ]; then
    echo -e "${YELLOW}⚙️  Creating watches.yaml from template...${NC}"
    cp config/watches.yaml.example config/watches.yaml
    echo -e "${RED}❌ Please edit config/watches.yaml with your searches!${NC}"
    exit 1
fi

# Validate configuration
echo -e "${BLUE}🔍 Validating configuration...${NC}"

# Check Discord webhook
if ! grep -q "https://discord.com/api/webhooks/" .env; then
    echo -e "${RED}❌ Discord webhook not configured in .env${NC}"
    exit 1
fi

# Check AI API key
if ! grep -q "sk-" .env && ! grep -q "sk-ant-" .env; then
    echo -e "${YELLOW}⚠️  No AI API key found. AI analysis will be disabled.${NC}"
fi

# Test system components
echo -e "${BLUE}🧪 Testing system components...${NC}"

# Test Discord webhook
echo -e "${BLUE}   Testing Discord webhook...${NC}"
if python -m app.main test-webhook > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Discord webhook working${NC}"
else
    echo -e "${RED}   ❌ Discord webhook failed${NC}"
    exit 1
fi

# Test domain access
echo -e "${BLUE}   Testing Vinted access...${NC}"
if python -m app.main test-domain vinted.fr > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Vinted access working${NC}"
else
    echo -e "${RED}   ❌ Vinted access failed (possible ban or network issue)${NC}"
    echo -e "${YELLOW}   Try again later or check your network connection${NC}"
fi

# Show configuration summary
echo -e "${BLUE}📋 Configuration Summary:${NC}"
echo -e "${BLUE}   Database: $(grep DATABASE_PATH .env | cut -d'=' -f2)${NC}"
echo -e "${BLUE}   Log Level: $(grep LOG_LEVEL .env | cut -d'=' -f2)${NC}"
echo -e "${BLUE}   Poll Interval: $(grep DEFAULT_POLL_INTERVAL_SEC .env | cut -d'=' -f2)s${NC}"
echo -e "${BLUE}   AI Provider: $(grep AI_PROVIDER .env | cut -d'=' -f2 2>/dev/null || echo 'openai')${NC}"

# Count watches
WATCH_COUNT=$(python -c "import yaml; print(len(yaml.safe_load(open('config/watches.yaml'))['watches']))" 2>/dev/null || echo "0")
echo -e "${BLUE}   Watches Configured: ${WATCH_COUNT}${NC}"

if [ "$WATCH_COUNT" -eq "0" ]; then
    echo -e "${RED}❌ No watches configured in config/watches.yaml${NC}"
    exit 1
fi

# Final confirmation
echo ""
echo -e "${GREEN}✅ All systems ready!${NC}"
echo -e "${BLUE}🎯 Starting AI-powered Vinted monitoring...${NC}"
echo -e "${YELLOW}   Press Ctrl+C to stop${NC}"
echo ""

# Start the monitor with optimized settings
export PYTHONUNBUFFERED=1
python -m app.main run
