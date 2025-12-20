# 🏗️ System Architecture

## Overview

This system implements a **microservices architecture** for cryptocurrency sentiment analysis using social media data, LLM inference, and machine learning predictions.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    Frontend (Node.js:3000)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend Services                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  API Server  │  │   Consumer   │  │  ML Service  │         │
│  │  (FastAPI)   │  │   (Kafka)    │  │   (MLflow)   │         │
│  │   Port 8000  │  │              │  │   Port 5001  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   MongoDB    │  │    Kafka     │  │   MinIO      │         │
│  │  Port 27017  │  │  Port 9092   │  │  Port 9000   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘         │
└─────────┼──────────────────┼─────────────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Workflow Orchestration                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Scheduler  │  │    Worker    │  │  Webserver   │         │
│  │              │  │              │  │  Port 8080   │         │
│  │    Airflow   │  │   Airflow    │  │   Airflow    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
│  • Google Gemini API (Sentiment Analysis)                       │
│  • Coinranking API (Price Data)                                 │
│  • Twitter/X (Social Media Data)                                │
│  • CoinMarketCap (News & Articles)                              │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Frontend Service
- **Technology**: Node.js + Express
- **Port**: 3000
- **Function**: 
  - Displays real-time sentiment trends
  - Shows cryptocurrency price predictions
  - Visualizes news and social media data

### 2. Backend Services

#### API Server (FastAPI)
- **Port**: 8000
- **Endpoints**:
  - `/cmc_news/` - CoinMarketCap news data
  - `/twitter/` - Twitter sentiment data
  - `/chart/` - Chart data for visualization
  - `/ml/` - ML prediction results
  - `/sentiment/` - Sentiment analysis via LLM

#### Consumer (Kafka Consumer)
- **Function**: Consumes messages from Kafka topics
- **Topics**:
  - `coinmarketcap-news` - News articles
  - `twitter-posts` - Social media posts
- **Action**: Processes and stores data in MongoDB

### 3. Data Layer

#### MongoDB
- **Port**: 27017
- **Collections**:
  - `coinmarketcap_news` - News articles
  - `twitter_posts` - Social media posts
  - `sentiment_results` - LLM analysis results
  - `ml_predictions` - Price predictions

#### Kafka
- **Ports**: 
  - 9092 (Internal - Docker network)
  - 9093 (External - Host access)
- **Topics**:
  - `coinmarketcap-news`
  - `twitter-posts`
- **Zookeeper**: Port 2181

#### MinIO (S3-compatible storage)
- **Port**: 9000, 9001 (Console)
- **Function**: Stores MLflow artifacts

### 4. Workflow Orchestration (Apache Airflow)

#### Airflow Webserver
- **Port**: 8080
- **Credentials**: `airflow` / `airflow`

#### DAGs (Data Pipelines)
1. **`cmc_news_24h`**: Crawls CoinMarketCap news every 24 hours
2. **`twitter_new_1h`**: Crawls Twitter posts every 1 hour
3. **`data_constructor_2h`**: Constructs training datasets every 2 hours
4. **`data_labeling_2h`**: Labels data using LLM every 2 hours
5. **`ml_train_2d`**: Trains ML models every 2 days

### 5. ML Tracking (MLflow)
- **Port**: 5001
- **Function**:
  - Experiment tracking
  - Model versioning
  - Hyperparameter tuning
  - Model registry

## Data Flow

### 1. Data Collection Flow
```
CoinMarketCap/Twitter → Airflow DAG → Kafka Producer 
  → Kafka Topic → Backend Consumer → MongoDB
```

### 2. Sentiment Analysis Flow
```
MongoDB (Raw Posts) → Airflow DAG → LLM API (Gemini) 
  → Sentiment Labels → MongoDB (Labeled Data)
```

### 3. ML Training Flow
```
MongoDB (Labeled Data) → Airflow DAG → Data Constructor 
  → Feature Engineering → MLflow → Trained Model → Model Registry
```

### 4. Prediction Flow
```
Frontend Request → Backend API → ML Model (from MLflow) 
  → Price Prediction → Frontend Display
```

## Network Configuration

All services run in the Docker network `sentiman-net`:

```yaml
networks:
  sentiman-net:
    driver: bridge
```

### Service Communication
- **Internal**: Services use Docker service names (e.g., `kafka:9092`, `mongodb:27017`)
- **External**: Host access via `localhost` (e.g., `localhost:8080`, `localhost:3000`)

### Kafka Dual-Listener Configuration
```yaml
KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka:9092,EXTERNAL://localhost:9093
KAFKA_LISTENERS: INTERNAL://0.0.0.0:9092,EXTERNAL://0.0.0.0:9093
```

- **INTERNAL (kafka:9092)**: For Docker services (Airflow, Backend)
- **EXTERNAL (localhost:9093)**: For host machine access

## Security

- Environment variables for API keys (`.env` file)
- MongoDB with authentication (optional)
- MinIO access keys
- Airflow secret key for session management

## Scalability

- **Horizontal Scaling**: Add more Airflow workers
- **Message Queue**: Kafka for async processing
- **Database**: MongoDB for flexible schema
- **Storage**: MinIO for distributed file storage

## Monitoring & Health Checks

Each service has health checks configured in `docker-compose.yaml`:

```yaml
healthcheck:
  test: ["CMD-SHELL", "health_check_command"]
  interval: 10s
  timeout: 5s
  retries: 20
  start_period: 90s
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Node.js, Express, Chart.js |
| Backend | Python 3.10, FastAPI |
| LLM | Google Gemini 1.5 Flash |
| ML | Scikit-learn, MLflow |
| Orchestration | Apache Airflow 2.7.2 |
| Message Queue | Apache Kafka 7.3.0 |
| Database | MongoDB 7.0 |
| Storage | MinIO (S3-compatible) |
| Container | Docker, Docker Compose |

## Deployment

All services are containerized and orchestrated via `docker-compose.yaml`:

```bash
docker-compose up -d
```

See [SETUP.md](./SETUP.md) for detailed deployment instructions.

