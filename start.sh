#!/bin/bash

# NBA Betting Stats API - Quick Start Script
# This script sets up and runs the complete betting tracker system

echo "=========================================="
echo "🏀 NBA BETTING STATS API - QUICK START"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "1️⃣  Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "2️⃣  Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}ℹ️  Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo "3️⃣  Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Install dependencies
echo "4️⃣  Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}❌ Error installing dependencies${NC}"
    exit 1
fi
echo ""

# Initialize database
echo "5️⃣  Initializing database..."
python3 << EOF
from nba_betting_stats_api import NBABettingStatsAPI
api = NBABettingStatsAPI()
print("Database initialized!")
EOF
echo -e "${GREEN}✓ Database ready${NC}"
echo ""

# Start the Flask server
echo "=========================================="
echo "🚀 STARTING API SERVER"
echo "=========================================="
echo ""
echo "API will be available at: http://localhost:5000"
echo "Demo page: Open demo.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask
python3 flask_api_base44.py
