# Environment Variables Templates

## Hướng dẫn: Copy các template dưới đây vào file .env tương ứng

---

## 📁 airflow/.env

```bash
# Airflow Configuration
AIRFLOW_UID=50000
AIRFLOW_PROJ_DIR=.
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow

# MongoDB Configuration
URL_MONGODB=mongodb://localhost:27017
DB_NAME_ORAICHAIN=blog-data

# Kafka Configuration
KAFKA_HOST=kafka
KAFKA_PORT=9092
KAFKA_USERNAME=
KAFKA_PASSWORD=

# Discord Webhooks
DISCORD_WEBHOOK_URL_ERROR=https://discord.com/api/webhooks/YOUR_ERROR_WEBHOOK
DISCORD_WEBHOOK_URL_SUCCESS=https://discord.com/api/webhooks/YOUR_SUCCESS_WEBHOOK
DISCORD_PLUME_WEBHOOK_URL_ERROR=https://discord.com/api/webhooks/YOUR_PLUME_ERROR_WEBHOOK
DISCORD_AGENT_MAX_WEBHOOK_URL_ERROR=https://discord.com/api/webhooks/YOUR_AGENT_MAX_ERROR_WEBHOOK
DISCORD_LOGO_ERROR=https://your-error-logo-url.com/logo.png
DISCORD_LOGO_SUCCESS=https://your-success-logo-url.com/logo.png
DISCORD_SERVER_NAME=Your Server Name

# Twitter/X API
TWITTER_AUTH_TOKEN=your_twitter_auth_token_here

# New York Times API
NEW_YORK_TIME_TOKEN=your_nyt_token_here

# Proxies (if needed)
PROXY_AUTH_USERNAME=your_proxy_username
PROXY_AUTH_PASSWORD=your_proxy_password

# Splash Service (if using)
SPLASH_HOST=http://splash:8050

# Environment
ENVIRONMENT=development

# Distilled MongoDB (if using)
MONGO_DATA_DISTILLED_URI=mongodb://localhost:27017
```

---

## 📁 backend/.env

```bash
# MongoDB Configuration
URL_MONGODB=mongodb://localhost:27017
DB_NAME=blog-data

# Kafka Configuration
KAFKA_HOST=kafka
KAFKA_PORT=9092

# Together AI API Key (for LLM sentiment analysis)
TOGETHER_API_KEY=your_together_ai_api_key_here

# Coinranking API Key (for Bitcoin price data)
COINRANKING_API_KEY=your_coinranking_api_key_here

# OpenAI API Key (if using OpenAI)
OPENAI_API_KEY=your_openai_api_key_here

# Discord Webhooks
DISCORD_WEBHOOK_URL_ERROR=https://discord.com/api/webhooks/YOUR_ERROR_WEBHOOK
DISCORD_WEBHOOK_URL_SUCCESS=https://discord.com/api/webhooks/YOUR_SUCCESS_WEBHOOK

# Environment
ENVIRONMENT=development

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 📁 kafka/.env

```bash
# Kafka Configuration
KAFKA_HOST=kafka
KAFKA_PORT=9092
KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181

# Kafka Topics
KAFKA_AUTO_CREATE_TOPICS_ENABLE=true
KAFKA_CREATE_TOPICS=coinmarketcap-news

# Kafka Retention Settings
KAFKA_LOG_RETENTION_HOURS=1
KAFKA_LOG_RETENTION_BYTES=4073741824
KAFKA_LOG_SEGMENT_BYTES=1073741824
KAFKA_RETENTION_CHECK_INTERVAL_MS=300000
```

---

## 📁 mlflow/.env

```bash
# PostgreSQL Configuration
POSTGRES_USER=mlflow
POSTGRES_PASSWORD=mlflow_password_change_me
POSTGRES_DB=mlflow

# MinIO Configuration (S3-compatible storage)
MINIO_ACCESS_KEY=minio_access_key_change_me
MINIO_SECRET_ACCESS_KEY=minio_secret_key_change_me
MLFLOW_S3_ENDPOINT=http://minio:9000

# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5001
```

---

## 🔑 Hướng dẫn lấy API Keys

### 1. **Together AI API Key** (Bắt buộc cho sentiment analysis)
- Đăng ký tại: https://api.together.xyz/
- Tạo API key trong dashboard
- Copy vào `TOGETHER_API_KEY`

### 2. **Coinranking API Key** (Bắt buộc cho Bitcoin price)
- Đăng ký tại: https://developers.coinranking.com/
- Lấy free API key
- Copy vào `COINRANKING_API_KEY`

### 3. **Discord Webhooks** (Optional - cho notifications)
- Vào Discord server settings
- Integrations → Webhooks → New Webhook
- Copy webhook URL

### 4. **Twitter/X Auth Token** (Nếu crawl Twitter)
- Đăng ký Twitter Developer Account
- Tạo app và lấy Bearer Token

### 5. **MongoDB**
- Nếu dùng MongoDB local: `mongodb://localhost:27017`
- Nếu dùng MongoDB Atlas: Lấy connection string từ cluster

---

## 📝 Quick Setup Commands

```bash
# Tạo các file .env
cd airflow && touch .env
cd ../backend && touch .env
cd ../kafka && touch .env
cd ../mlflow && touch .env

# Copy nội dung từ template trên vào từng file
```

---

## ⚠️ QUAN TRỌNG

1. **KHÔNG commit file .env** vào git (đã có trong .gitignore)
2. **Rotate các API keys** đã bị exposed trong code hiện tại
3. **Thay đổi tất cả passwords** mặc định trước khi deploy production
4. **Bảo mật MongoDB** với username/password nếu expose ra internet

---

## 🔒 Security Checklist

- [ ] Đã tạo tất cả file .env
- [ ] Đã thay thế tất cả `your_*_here` placeholders
- [ ] Đã rotate API keys bị exposed
- [ ] Đã set strong passwords cho databases
- [ ] Đã verify file .env không bị commit vào git
- [ ] Đã restrict MongoDB access
- [ ] Đã configure firewall cho production

