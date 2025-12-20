#!/bin/bash

# =============================================================================
# Restart All Services - Sentiment Analysis Project
# =============================================================================

# Colors
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}  Restarting All Services${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Stop all
./stop-all.sh

# Wait a bit
echo ""
echo "⏳ Waiting 5 seconds before restart..."
sleep 5

# Start all
./start-all.sh

