# 🚀 Setup Guide - Sentiment Analysis on Social Media for Cryptocurrency

## 📋 Prerequisites

### Required Software:
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Node.js**: Version 16 or higher (for frontend)
- **Git**: For cloning repository

### System Requirements:
- **RAM**: Minimum 8GB (16GB recommended)
- **CPU**: Minimum 4 cores
- **Disk Space**: Minimum 20GB free space
- **OS**: Linux, macOS, or Windows with WSL2

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (Node.js)                     │
│                     http://localhost:3000                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend API (FastAPI)                       │
│                   http://localhost:8000                      │
└─────────┬──────────────────────┬─────────────────┬──────────┘
          │                      │                 │
          ↓                      ↓                 ↓
┌─────────────────┐   ┌──────────────────┐   ┌──────────────┐
│   MongoDB       │   │   Kafka          │   │   MLflow     │
│   Port: 27017   │   │   Port: 9092     │   │   Port: 5001 │
└─────────────────┘   └──────────────────┘   └──────────────┘
          ↑                      ↑
          │                      │
          └──────────┬───────────┘
                     │
         ┌───────────────────────┐
         │   Airflow (Scheduler) │
         │   Port: 8080          │
         └───────────────────────┘
```

---

## 📦 Step-by-Step Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/ML-K67-HUST/Sentiment-Analysis-on-Social-Media-for-cryptocurrency.git
cd Sentiment-Analysis-on-Social-Media-for-cryptocurrency
```

### Step 2: Create Docker Network

```bash
docker network create net
```

### Step 3: Configure Environment Variables

#### 3.1 Tạo file .env cho mỗi service

```bash
# Airflow
cd airflow
touch .env
# Copy nội dung từ ENV_TEMPLATES.md vào file này

# Backend
cd ../backend
touch .env
# Copy nội dung từ ENV_TEMPLATES.md vào file này

# Kafka
cd ../kafka
touch .env
# Copy nội dung từ ENV_TEMPLATES.md vào file này

# MLflow
cd ../mlflow
touch .env
# Copy nội dung từ ENV_TEMPLATES.md vào file này

cd ..
```

#### 3.2 Configure API Keys

**Bắt buộc phải có:**
1. **Together AI API Key**: Đăng ký tại https://api.together.xyz/
2. **Coinranking API Key**: Đăng ký tại https://developers.coinranking.com/

**Optional:**
- Discord Webhooks (for notifications)
- Twitter API Token (if crawling Twitter)

Xem chi tiết trong `ENV_TEMPLATES.md`

### Step 4: Fix Hardcoded Secrets

⚠️ **QUAN TRỌNG**: Cần refactor các API keys hardcoded trong code

#### 4.1 Fix backend/LLM/sentiment_agent.py

Thay thế dòng 9:
```python
# BAD - HARDCODED
TOGETHER_API_KEY = "54f853e31dcf2a608cdd6a11a05ab5bd3c5212add172fc1a3a9eb557d6da4ab3"

# GOOD - USE ENV VAR
import os
from dotenv import load_dotenv
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
```

#### 4.2 Fix backend/data_constructor.py

Thay thế dòng 9:
```python
# BAD - HARDCODED
'x-access-token': 'coinrankingcf28de3a1e8ccdad31ea8cb51ed9f8e4a98df79b535570a1'

# GOOD - USE ENV VAR
import os
from dotenv import load_dotenv
load_dotenv()
'x-access-token': os.getenv("COINRANKING_API_KEY")
```

### Step 5: Start MongoDB (if not using external)

```bash
docker run -d \
  --name mongodb \
  --network net \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:latest
```

### Step 6: Start Kafka

```bash
cd kafka
docker-compose up -d
cd ..
```

Verify Kafka is running:
```bash
docker ps | grep kafka
```

### Step 7: Start MLflow

```bash
cd mlflow
docker-compose up -d --build
cd ..
```

Access MLflow UI: http://localhost:5001

### Step 8: Start Airflow

```bash
cd airflow

# Build custom Airflow image
docker build . --tag sentiman_airflow:0.1

# Initialize Airflow database
docker-compose up airflow-init

# Start all Airflow services
docker-compose up -d
cd ..
```

Access Airflow UI: http://localhost:8080
- Username: `airflow`
- Password: `airflow`

### Step 9: Start Backend

```bash
cd backend
docker-compose up -d --build
cd ..
```

Verify backend is running:
```bash
curl http://localhost:8000/
# Should return: {"message":"ok"}
```

### Step 10: Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Access Frontend: http://localhost:3000

---

## ✅ Verification Checklist

### Check all services are running:

```bash
# Check Docker containers
docker ps

# Expected containers:
# - sentiman-airflow-webserver
# - sentiman-airflow-scheduler
# - sentiman-airflow-worker
# - sentiman-airflow-triggerer
# - postgres (Airflow DB)
# - redis
# - ktech_kafka
# - ktech_zookeeper
# - sentiman_consumer (backend)
# - mlflow_server
# - minio
# - postgres (MLflow DB)
# - mongodb (if running locally)
```

### Test each service:

```bash
# Test Airflow
curl http://localhost:8080/health

# Test Backend API
curl http://localhost:8000/

# Test MLflow
curl http://localhost:5001/

# Test Kafka
docker exec -it ktech_kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

---

## 🔧 Troubleshooting

### Issue 1: Docker network not found
```bash
Error: network net not found
```
**Solution**: 
```bash
docker network create net
```

### Issue 2: Port already in use
```bash
Error: Bind for 0.0.0.0:8080 failed: port is already allocated
```
**Solution**: 
- Stop service using that port
- Or change port in docker-compose.yaml

### Issue 3: MongoDB connection failed
```bash
Error: pymongo.errors.ServerSelectionTimeoutError
```
**Solution**:
- Check MongoDB is running: `docker ps | grep mongo`
- Verify connection string in .env
- Check network connectivity

### Issue 4: Kafka consumer not receiving messages
**Solution**:
- Check Kafka is running
- Verify topic exists: `docker exec -it ktech_kafka kafka-topics.sh --list --bootstrap-server localhost:9092`
- Check producer is sending messages

### Issue 5: Airflow DAGs not appearing
**Solution**:
- Check DAG files have no syntax errors
- Refresh Airflow UI
- Check scheduler logs: `docker logs sentiman-airflow-scheduler`

### Issue 6: API keys not working
**Solution**:
- Verify .env files exist in correct locations
- Rotate old exposed API keys
- Restart containers after changing .env

---

## 📊 Usage Guide

### 1. Monitor Airflow DAGs

1. Open http://localhost:8080
2. Check DAGs are enabled:
   - `cmc_news_24h`: Crawls CoinMarketCap articles every hour
   - `data_constructor_2h`: Constructs dataset every 2 hours
   - `data_labeling_2h`: Labels data every 2 hours
   - `ml_train_2d`: Trains ML model every 2 days

### 2. View Sentiment Analysis Results

1. Open Frontend: http://localhost:3000
2. Select "CoinMarketCap" or "X" tab
3. View analyzed articles with sentiment scores

### 3. Track ML Experiments

1. Open MLflow: http://localhost:5001
2. View experiment runs
3. Compare model metrics

### 4. API Endpoints

- `GET /`: Health check
- `GET /cmc_news/`: Get CoinMarketCap news with sentiment
- `GET /x_news/`: Get X/Twitter news with sentiment
- `GET /chart/`: Get Bitcoin price chart data

---

## 🛑 Stopping Services

```bash
# Stop Frontend
# Press Ctrl+C in frontend terminal

# Stop Backend
cd backend && docker-compose down && cd ..

# Stop Airflow
cd airflow && docker-compose down && cd ..

# Stop Kafka
cd kafka && docker-compose down && cd ..

# Stop MLflow
cd mlflow && docker-compose down && cd ..

# Stop MongoDB (if started manually)
docker stop mongodb
docker rm mongodb

# Remove network (optional)
docker network rm net
```

---

## 🔄 Daily Operations

### Start all services:
```bash
# Start infrastructure
cd kafka && docker-compose up -d && cd ..
cd mlflow && docker-compose up -d && cd ..

# Start Airflow
cd airflow && docker-compose up -d && cd ..

# Start Backend
cd backend && docker-compose up -d && cd ..

# Start Frontend
cd frontend && npm run dev
```

### View logs:
```bash
# Airflow scheduler logs
docker logs -f sentiman-airflow-scheduler

# Backend logs
docker logs -f sentiman_consumer

# Kafka logs
docker logs -f ktech_kafka
```

---

## 📝 Next Steps

1. ✅ Setup complete
2. Configure Discord webhooks for notifications (optional)
3. Add Twitter API token for Twitter crawling (optional)
4. Monitor DAG runs in Airflow
5. Check sentiment analysis results in Frontend
6. Train and deploy ML models

---

## 🆘 Getting Help

- Check `PROJECT_ANALYSIS.md` for known issues
- Review `ENV_TEMPLATES.md` for configuration details
- Check container logs for errors
- Open GitHub issue if you find bugs

---

## 📚 Additional Resources

- [Airflow Documentation](https://airflow.apache.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)

---

**Happy Analyzing! 📈🚀**

