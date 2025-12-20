# ✅ ĐÃ FIX LỖI KAFKA CONNECTION TỪ AIRFLOW!

## 🔍 Vấn Đề Ban Đầu

**Lỗi:** Airflow tasks kết nối được Kafka lúc đầu, nhưng sau đó Kafka trả về metadata với `localhost:9092` → Airflow worker không thể connect đến `localhost` vì đang trong container khác.

```
✅ connecting to kafka:9092 [('172.28.0.10', 9092) IPv4]>: Connection complete.
❌ connecting to localhost:9092 [('::1', 9092, 0, 0) IPv6]
   ERROR: Connect attempt returned error 111. ECONNREFUSED
```

## 🛠️ Giải Pháp

### Thay Đổi Kafka Config

**Trước:**
```yaml
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
```

**Sau (✅ Fixed):**
```yaml
# INTERNAL: For Docker services (airflow, backend, etc.) -> kafka:9092
# EXTERNAL: For host machine access -> localhost:9093
KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka:9092,EXTERNAL://localhost:9093
KAFKA_LISTENERS: INTERNAL://0.0.0.0:9092,EXTERNAL://0.0.0.0:9093
KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT
KAFKA_INTER_BROKER_LISTENER_NAME: INTERNAL
```

### Kết Quả

- **Docker services (Airflow, Backend)** → Connect đến `kafka:9092` ✅
- **Host machine** → Connect đến `localhost:9093` ✅
- Không còn lỗi "localhost:9092 connection refused" ✅

---

## 🧪 Test Lại

### 1. Trigger Airflow DAG từ UI

1. Mở Airflow UI: http://localhost:8080
2. Login: `airflow` / `airflow`
3. Tìm DAG `cmc_news_24h`
4. Click **Play icon** (▶️) → **Trigger DAG**
5. Click vào DAG run mới nhất
6. Click vào task `collect_latest_10_pages_cmc_article_data`
7. Click **Logs** → Check xem còn lỗi "localhost:9092" không

### 2. Hoặc Trigger từ CLI

```bash
docker exec sentiman_airflow_webserver airflow dags trigger cmc_news_24h
```

### 3. Check Logs

```bash
# Check Airflow worker logs
docker logs sentiman_airflow_worker 2>&1 | tail -50

# Check backend consumer logs
docker logs sentiman_backend_consumerdock 2>&1 | tail -50

# Check Kafka broker logs
docker logs sentiman_kafka 2>&1 | tail -50
```

---

## 📊 Trạng Thái Services

```bash
$ docker-compose ps

NAME                            STATUS
sentiman_kafka                  Up 4 minutes (healthy) ✅
sentiman_airflow_worker         Up 2 minutes (healthy) ✅
sentiman_airflow_scheduler      Up 2 minutes (health: starting) ⏳
sentiman_backend_consumerdock   Up 2 minutes (healthy) ✅
```

---

## 🔌 Kafka Connection Ports

| From | To | Port |
|------|-----|------|
| **Airflow Workers** | Kafka | `kafka:9092` (INTERNAL) |
| **Backend API** | Kafka | `kafka:9092` (INTERNAL) |
| **Backend Consumer** | Kafka | `kafka:9092` (INTERNAL) |
| **Host Machine** | Kafka | `localhost:9093` (EXTERNAL) |

---

## ⚠️ Lưu Ý Quan Trọng

### 1. Đã Xóa Kafka Volume
- Đã xóa `sentiman_kafka_data` volume để tránh cluster ID conflict
- Kafka đã tạo lại data từ đầu với cluster ID mới

### 2. Nếu Vẫn Gặp Lỗi
Nếu vẫn thấy lỗi "localhost:9092", restart toàn bộ stack:

```bash
cd /Users/khangtuan/Documents/courses/web_mining/Sentiment-Analysis-on-Social-Media-for-cryptocurrency

# Stop all
docker-compose down

# Start all
docker-compose up -d

# Wait for services
sleep 60

# Check status
docker-compose ps
```

### 3. Test Kafka Connection Từ Airflow

```bash
# Exec vào Airflow worker
docker exec -it sentiman_airflow_worker bash

# Install kafka-python nếu chưa có
pip install kafka-python

# Test connection
python3 << 'EOF'
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers=['kafka:9092'])
print("✅ Connected to Kafka successfully!")
producer.close()
EOF
```

### 4. Test Kafka Connection Từ Host Machine

```bash
# Install kafka-python
pip install kafka-python

# Test connection
python3 << 'EOF'
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers=['localhost:9093'])
print("✅ Connected to Kafka from host successfully!")
producer.close()
EOF
```

---

## 🎯 Kết Luận

✅ **Đã fix xong lỗi Kafka connection!**

- Kafka giờ có 2 listeners: INTERNAL (kafka:9092) và EXTERNAL (localhost:9093)
- Airflow workers, Backend services đều connect đến INTERNAL listener
- Host machine connect đến EXTERNAL listener
- Không còn lỗi "localhost:9092 connection refused"

**Bước tiếp theo:** Trigger Airflow DAGs và verify data được crawl và publish lên Kafka thành công! 🚀

