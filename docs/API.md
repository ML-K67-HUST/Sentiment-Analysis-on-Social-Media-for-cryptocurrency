# 📡 API Documentation

Complete REST API reference for the Cryptocurrency Sentiment Analysis system.

## Base URL

```
http://localhost:8000
```

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Endpoints

### 1. Health Check

#### `GET /health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy"
}
```

---

### 2. CoinMarketCap News

#### `GET /cmc_news/`

Retrieve cryptocurrency news articles from CoinMarketCap.

**Query Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `limit` | integer | No | Number of articles to return | 10 |
| `skip` | integer | No | Number of articles to skip (pagination) | 0 |
| `symbol` | string | No | Filter by crypto symbol (e.g., "BTC") | All |

**Example Request:**
```bash
curl "http://localhost:8000/cmc_news/?limit=5&symbol=BTC"
```

**Response:**
```json
{
  "total": 150,
  "data": [
    {
      "_id": "68fe3bf50b75251b9da81adb",
      "title": "Bitcoin Surges Past $70,000",
      "content": "Bitcoin reached a new high...",
      "source": "CoinMarketCap",
      "published_at": "2025-10-26T10:30:00Z",
      "crypto_symbols": ["BTC"],
      "url": "https://coinmarketcap.com/...",
      "sentiment": "positive"
    }
  ]
}
```

---

### 3. Twitter/Social Media Data

#### `GET /twitter/`

Retrieve sentiment analysis from Twitter posts.

**Query Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `limit` | integer | No | Number of posts to return | 10 |
| `skip` | integer | No | Number of posts to skip | 0 |
| `symbol` | string | No | Filter by crypto symbol | All |
| `sentiment` | string | No | Filter by sentiment (positive/negative/neutral) | All |

**Example Request:**
```bash
curl "http://localhost:8000/twitter/?symbol=BTC&sentiment=positive&limit=20"
```

**Response:**
```json
{
  "total": 1250,
  "data": [
    {
      "_id": "tweet_123456",
      "text": "Bitcoin is looking bullish! 🚀",
      "author": "crypto_trader",
      "created_at": "2025-10-26T15:20:00Z",
      "crypto_symbols": ["BTC"],
      "sentiment": "positive",
      "sentiment_score": 0.85,
      "retweets": 45,
      "likes": 230
    }
  ]
}
```

---

### 4. Sentiment Analysis (LLM)

#### `POST /sentiment/analyze`

Analyze sentiment of text using LLM (Gemini or Together AI).

**Request Body:**
```json
{
  "text": "Bitcoin price is going to the moon! 🚀",
  "crypto_symbol": "BTC"
}
```

**Response:**
```json
{
  "text": "Bitcoin price is going to the moon! 🚀",
  "sentiment": "positive",
  "confidence": 0.92,
  "reasoning": "The text expresses strong optimism about Bitcoin price movement",
  "crypto_symbol": "BTC",
  "analyzed_at": "2025-10-26T16:30:00Z"
}
```

---

### 5. Chart Data

#### `GET /chart/`

Retrieve historical chart data for visualization.

**Query Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `symbol` | string | Yes | Crypto symbol (e.g., "BTC") | - |
| `timeframe` | string | No | Time period (1h/24h/7d/30d) | 24h |
| `data_type` | string | No | Type (price/sentiment/volume) | price |

**Example Request:**
```bash
curl "http://localhost:8000/chart/?symbol=BTC&timeframe=7d&data_type=price"
```

**Response:**
```json
{
  "symbol": "BTC",
  "timeframe": "7d",
  "data": [
    {
      "timestamp": "2025-10-20T00:00:00Z",
      "price": 67500.00,
      "volume": 28500000000,
      "sentiment_score": 0.72
    },
    {
      "timestamp": "2025-10-21T00:00:00Z",
      "price": 68200.00,
      "volume": 30200000000,
      "sentiment_score": 0.78
    }
  ]
}
```

---

### 6. ML Predictions

#### `GET /ml/predict`

Get cryptocurrency price predictions from ML models.

**Query Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `symbol` | string | Yes | Crypto symbol (e.g., "BTC") | - |
| `horizon` | string | No | Prediction horizon (1h/24h/7d) | 24h |
| `model` | string | No | Model name (ridge/gradient_boosting) | ridge |

**Example Request:**
```bash
curl "http://localhost:8000/ml/predict?symbol=BTC&horizon=24h"
```

**Response:**
```json
{
  "symbol": "BTC",
  "current_price": 68200.00,
  "predicted_price": 69500.00,
  "change_percent": 1.91,
  "confidence_interval": {
    "lower": 68000.00,
    "upper": 71000.00
  },
  "model": "ridge_cv_best",
  "prediction_time": "2025-10-26T17:00:00Z",
  "horizon": "24h"
}
```

#### `GET /ml/models`

List available ML models and their performance metrics.

**Response:**
```json
{
  "models": [
    {
      "name": "ridge_cv_best",
      "type": "regression",
      "mse": 0.00145,
      "r2_score": 0.87,
      "trained_at": "2025-10-24T10:00:00Z",
      "features": ["sentiment_score", "volume", "price_lag_1h"]
    },
    {
      "name": "gradient_boosting_best",
      "type": "regression",
      "mse": 0.00132,
      "r2_score": 0.89,
      "trained_at": "2025-10-24T10:30:00Z"
    }
  ]
}
```

---

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid parameter: symbol must be a valid crypto symbol"
}
```

### 404 Not Found
```json
{
  "detail": "No data found for symbol: INVALID"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Database connection failed: timeout"
}
```

### 503 Service Unavailable
```json
{
  "detail": "LLM service temporarily unavailable, please try again"
}
```

---

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Burst**: 20 requests per second
- **Headers**:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 85
  X-RateLimit-Reset: 1698345600
  ```

---

## Authentication

Currently, the API is open for development. For production:

```bash
# Add API key to request headers
curl -H "X-API-Key: your_api_key" http://localhost:8000/twitter/
```

---

## WebSocket (Future)

Real-time data streaming will be available via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/realtime');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New sentiment data:', data);
};
```

---

## Examples

### Python
```python
import requests

# Get latest Bitcoin news
response = requests.get(
    'http://localhost:8000/cmc_news/',
    params={'symbol': 'BTC', 'limit': 5}
)
news = response.json()

# Analyze sentiment
response = requests.post(
    'http://localhost:8000/sentiment/analyze',
    json={
        'text': 'Bitcoin to the moon!',
        'crypto_symbol': 'BTC'
    }
)
sentiment = response.json()
print(f"Sentiment: {sentiment['sentiment']}")
```

### JavaScript
```javascript
// Fetch chart data
fetch('http://localhost:8000/chart/?symbol=BTC&timeframe=7d')
  .then(response => response.json())
  .then(data => {
    console.log('Chart data:', data);
  });

// Get ML prediction
fetch('http://localhost:8000/ml/predict?symbol=BTC')
  .then(response => response.json())
  .then(prediction => {
    console.log(`Predicted price: $${prediction.predicted_price}`);
  });
```

### cURL
```bash
# Get Twitter sentiment
curl -X GET "http://localhost:8000/twitter/?symbol=ETH&sentiment=positive" \
  -H "accept: application/json"

# Analyze text sentiment
curl -X POST "http://localhost:8000/sentiment/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Ethereum upgrade is amazing!",
    "crypto_symbol": "ETH"
  }'
```

---

## SDKs (Future)

Official SDKs will be available for:
- Python (`pip install sentiman-sdk`)
- JavaScript/TypeScript (`npm install sentiman-sdk`)
- Go (`go get github.com/sentiman/sdk-go`)

---

For more details, visit the interactive API documentation at http://localhost:8000/docs

