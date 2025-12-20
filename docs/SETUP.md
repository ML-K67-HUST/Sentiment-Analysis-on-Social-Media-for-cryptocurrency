# 📦 Setup Guide

Complete guide to set up and run the Cryptocurrency Sentiment Analysis system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Starting Services](#starting-services)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Node.js**: Version 16+ (for frontend)
- **npm**: Version 7+ (comes with Node.js)

### Installation Links

- Docker: https://docs.docker.com/get-docker/
- Node.js: https://nodejs.org/

### Verify Installation

```bash
docker --version          # Should show 20.10+
docker-compose --version  # Should show 2.0+
node --version            # Should show v16+
npm --version             # Should show 7+
```

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/ML-K67-HUST/Sentiment-Analysis-on-Social-Media-for-cryptocurrency.git
cd Sentiment-Analysis-on-Social-Media-for-cryptocurrency
```

### Step 2: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Configuration

### Step 1: Create Environment File

```bash
cp .env.example .env
```

### Step 2: Edit `.env` File

Open `.env` in your favorite editor and configure the following:

#### **Required API Keys**

```bash
# ============================================
# LLM Provider Configuration
# ============================================
# Options: "gemini" or "together"
LLM_PROVIDER=gemini

# Google Gemini API (RECOMMENDED - FREE)
# Get your key: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Together AI API (Optional - Paid)
# Get your key: https://api.together.xyz/
TOGETHER_API_KEY=your_together_api_key_here

# ============================================
# Cryptocurrency Data API
# ============================================
# Coinranking API (FREE tier available)
# Get your key: https://developers.coinranking.com/
COINRANKING_API_KEY=your_coinranking_api_key_here
```

#### **Optional Configurations**

```bash
# ============================================
# Database Configuration
# ============================================
MONGODB_CONNECTION_STRING=mongodb://mongodb:27017
MONGODB_DATABASE=twitter_crawler

# ============================================
# Kafka Configuration
# ============================================
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_LOG_RETENTION_HOURS=24
KAFKA_LOG_RETENTION_BYTES=4073741824
KAFKA_LOG_SEGMENT_BYTES=1073741824

# ============================================
# Airflow Configuration
# ============================================
AIRFLOW_UID=50000
AIRFLOW__CORE__FERNET_KEY=your_fernet_key_here
AIRFLOW__WEBSERVER__SECRET_KEY=your_secret_key_here

# ============================================
# MLflow Configuration
# ============================================
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin123
MLFLOW_S3_ENDPOINT_URL=http://minio:9000
```

### API Key Setup Guides

#### 1. Google Gemini API (Recommended - FREE)

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste into `.env`

**Why Gemini?**
- ✅ Free to use
- ✅ Fast (1-2 second response)
- ✅ Excellent quality
- ✅ No credit card required

#### 2. Coinranking API

1. Go to https://developers.coinranking.com/
2. Sign up for a free account
3. Navigate to "API Keys" section
4. Copy your API key and paste into `.env`

**Free Tier:**
- 10,000 requests/month
- Sufficient for most use cases

---

## Starting Services

### Option 1: Using Helper Scripts (Recommended)

#### Start All Services
```bash
./scripts/start-all.sh
```

This will:
1. Start all Docker services
2. Start the frontend Node.js server
3. Display service status

#### Stop All Services
```bash
./scripts/stop-all.sh
```

#### Restart All Services
```bash
./scripts/restart-all.sh
```

#### Clean Restart (Remove volumes)
```bash
./scripts/stop-all.sh --clean
./scripts/start-all.sh
```

### Option 2: Using Make Commands

```bash
# Start all services
make quick-start

# Stop all services
make stop

# Restart services
make restart

# View logs
make logs

# Check service health
make health
```

### Option 3: Manual Docker Compose

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (clean restart)
docker-compose down -v
```

---

## Verification

### Step 1: Check Service Health

```bash
docker-compose ps
```

All services should show **"healthy"** status:

```
NAME                        STATUS
sentiman_mongodb            Up (healthy)
sentiman_kafka              Up (healthy)
sentiman_backend_api        Up (healthy)
sentiman_airflow_webserver  Up (healthy)
sentiman_mlflow             Up (healthy)
...
```

### Step 2: Access Web Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | N/A |
| **Backend API** | http://localhost:8000/docs | N/A |
| **Airflow** | http://localhost:8080 | airflow / airflow |
| **MLflow** | http://localhost:5001 | N/A |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin123 |

### Step 3: Test Backend API

```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy"}
```

### Step 4: Verify Data Pipeline

1. **Open Airflow UI**: http://localhost:8080
2. **Login**: `airflow` / `airflow`
3. **Check DAGs**: You should see 5 DAGs:
   - `cmc_news_24h` - CoinMarketCap news crawler
   - `twitter_new_1h` - Twitter posts crawler
   - `data_constructor_2h` - Dataset construction
   - `data_labeling_2h` - LLM labeling
   - `ml_train_2d` - Model training

4. **Trigger a DAG**:
   - Click on `cmc_news_24h`
   - Click the **▶️ Play icon**
   - Click **Trigger DAG**
   - Monitor the task execution

5. **Check logs**:
   - Click on the running task
   - Click **Logs**
   - Verify no errors (especially Kafka connection)

---

## Troubleshooting

### Common Issues

#### 1. Kafka Connection Refused

**Symptom**: Airflow logs show `localhost:9092: [Errno 111] Connection refused`

**Solution**:
```bash
# Clean restart with volume removal
docker-compose down -v
docker-compose up -d
```

**Why**: Old Kafka data conflicts with new cluster ID.

#### 2. MongoDB Connection Error

**Symptom**: Backend API shows `Connection refused localhost:27017`

**Solution**:
Check that `.env` has correct connection string:
```bash
MONGODB_CONNECTION_STRING=mongodb://mongodb:27017
```

Rebuild backend:
```bash
docker-compose up -d --build backend-api
```

#### 3. Services Not Healthy

**Symptom**: `docker-compose ps` shows "unhealthy" status

**Solution**:
```bash
# Check specific service logs
docker logs sentiman_<service_name>

# Example:
docker logs sentiman_kafka
docker logs sentiman_mongodb
```

#### 4. Frontend Not Accessible

**Symptom**: Cannot access http://localhost:3000

**Solution**:
```bash
# Check if frontend is running
ps aux | grep "node server.js"

# Restart frontend manually
cd frontend
node server.js &
```

Or use the helper script:
```bash
./scripts/start-all.sh
```

#### 5. Insufficient Disk Space

**Symptom**: Services fail to start with "no space left" error

**Solution**:
```bash
# Remove unused Docker resources
docker system prune -a --volumes

# WARNING: This removes ALL unused Docker data
```

### Health Check Commands

```bash
# View all service status
docker-compose ps

# Check specific service health
docker inspect sentiman_kafka --format='{{json .State.Health}}' | jq .

# View service logs (last 50 lines)
docker logs --tail 50 sentiman_kafka

# Follow logs in real-time
docker logs -f sentiman_backend_api

# Check network connectivity
docker exec sentiman_airflow_worker ping kafka -c 3
```

### Reset Everything

If you want to start completely fresh:

```bash
# Stop all services and remove volumes
docker-compose down -v

# Remove all Docker containers, images, and volumes
docker system prune -a --volumes

# Restart from scratch
docker-compose up -d
```

---

## Next Steps

- Read [ARCHITECTURE.md](./ARCHITECTURE.md) to understand the system design
- Check [API.md](./API.md) for API documentation
- See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for more common issues
- View [CONTRIBUTING.md](./CONTRIBUTING.md) to contribute to the project

