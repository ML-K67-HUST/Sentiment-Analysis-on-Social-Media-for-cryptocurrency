#!/bin/bash

# =============================================================================
# Stop All Services - Sentiment Analysis Project
# =============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}  Stopping All Services${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Step 1: Stop Frontend
echo -e "${YELLOW}🎨 Stopping Frontend...${NC}"

# Method 1: Kill by PID file
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo -e "${GREEN}✅ Frontend stopped (PID: $FRONTEND_PID)${NC}"
        rm logs/frontend.pid
    else
        echo -e "${YELLOW}⚠️  Frontend process not found${NC}"
        rm logs/frontend.pid
    fi
fi

# Method 2: Kill by port
FRONTEND_PIDS=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo "$FRONTEND_PIDS" | xargs kill 2>/dev/null
    echo -e "${GREEN}✅ Frontend processes on port 3000 killed${NC}"
else
    echo -e "${GREEN}✅ No frontend process running on port 3000${NC}"
fi

# Step 2: Stop Docker services
echo ""
echo -e "${YELLOW}🐳 Stopping Docker services...${NC}"
docker-compose down

echo ""
echo -e "${GREEN}✅ All services stopped!${NC}"
echo ""
echo -e "${BLUE}To start again:${NC} ./start-all.sh"
echo ""

