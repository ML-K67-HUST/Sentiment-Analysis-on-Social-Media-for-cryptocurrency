#!/bin/bash

# =============================================================================
# Start All Services - Sentiment Analysis Project
# =============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}  Starting All Services${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo -e "${YELLOW}   Create .env file from .env.example first${NC}"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Start Docker services
echo -e "${YELLOW}📦 Starting Docker services...${NC}"
docker-compose up -d

echo ""
echo -e "${YELLOW}⏳ Waiting for services to start (60s)...${NC}"
echo -e "${YELLOW}   This may take a while on first start...${NC}"
sleep 60

# Step 2: Check service status
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
docker-compose ps

# Step 3: Start Frontend
echo ""
echo -e "${YELLOW}🎨 Starting Frontend...${NC}"

# Check if frontend is already running
if lsof -ti:3000 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Frontend already running on port 3000${NC}"
else
    cd frontend
    nohup node server.js > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    cd ..
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
fi

# Wait a bit
sleep 3

# Step 4: Verify services
echo ""
echo -e "${BLUE}🔍 Verifying Services...${NC}"
echo ""

# Check Frontend
if curl -s http://localhost:3000/ > /dev/null; then
    echo -e "${GREEN}✅ Frontend:${NC}     http://localhost:3000"
else
    echo -e "${RED}❌ Frontend:${NC}     Not responding"
fi

# Check Backend API
if curl -s http://localhost:8000/ > /dev/null; then
    echo -e "${GREEN}✅ Backend API:${NC}  http://localhost:8000"
else
    echo -e "${RED}❌ Backend API:${NC}  Not responding"
fi

# Check Airflow
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Airflow:${NC}      http://localhost:8080"
else
    echo -e "${YELLOW}⏳ Airflow:${NC}      Starting... (may take 1-2 minutes)"
fi

# Check MLflow
if curl -s http://localhost:5001/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MLflow:${NC}       http://localhost:5001"
else
    echo -e "${YELLOW}⏳ MLflow:${NC}       Starting..."
fi

echo ""
echo -e "${BLUE}=============================================${NC}"
echo -e "${GREEN}🎉 All Services Started!${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "  🎨 Frontend:    http://localhost:3000"
echo -e "  📡 Backend:     http://localhost:8000"
echo -e "  🔄 Airflow:     http://localhost:8080  (airflow/airflow)"
echo -e "  📊 MLflow:      http://localhost:5001"
echo -e "  💾 MinIO:       http://localhost:9001  (minioadmin/minioadmin123)"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo -e "  1. Enable Airflow DAGs at http://localhost:8080"
echo -e "  2. Trigger DAGs manually for first run"
echo -e "  3. Wait 10-15 minutes for data collection"
echo -e "  4. View results at http://localhost:3000"
echo ""
echo -e "${BLUE}View logs:${NC}"
echo -e "  Backend:   docker logs -f sentiman_backend_api"
echo -e "  Consumer:  docker logs -f sentiman_backend_consumer"
echo -e "  Frontend:  tail -f logs/frontend.log"
echo ""
echo -e "${BLUE}Stop all:${NC} ./stop-all.sh"
echo ""

