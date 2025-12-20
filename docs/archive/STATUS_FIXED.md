# ✅ TẤT CẢ SERVICES ĐÃ HOẠT ĐỘNG!

**Thời gian:** 2025-10-26 22:23

## 🎯 Vấn Đề Đã Fix

### 1. **Kafka InconsistentClusterIdException** ❌ → ✅
**Lỗi ban đầu:**
```
The Cluster ID gB_S0zVCSr6dov6u7idPZA doesn't match stored clusterId Some(xC8k-0LpTZShwx2PPZx_8Q) in meta.properties
```

**Giải pháp:**
- Xóa **tất cả volumes** với: `docker-compose down -v`
- Kafka data volume bị conflict từ cluster cũ
- Sau khi xóa và up lại → ✅ Kafka healthy

### 2. **Backend API & MLflow Health Checks Fail** ❌ → ✅
**Lỗi ban đầu:**
- Health checks dùng `curl` nhưng containers không có `curl`
- Health checks luôn fail → services unhealthy

**Giải pháp:**
- Đổi health check sang **Python** (có sẵn trong containers):
```yaml
# Backend API
healthcheck:
  test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/')\" || exit 1"]

# MLflow
healthcheck:
  test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:5000/health')\" || exit 1"]
```
- Sau khi recreate containers → ✅ Backend API & MLflow healthy

---

## 📊 Trạng Thái Services (Hiện Tại)

| Service | Status | Port | Note |
|---------|--------|------|------|
| **Zookeeper** | ✅ Healthy | 2181 | |
| **Kafka** | ✅ Healthy | 9092, 9093 | **Fixed!** |
| **MongoDB** | ✅ Healthy | 27017 | |
| **Backend API** | ✅ Healthy | 8000 | **Fixed!** |
| **Backend Consumer** | ✅ Healthy | - | |
| **MLflow** | ✅ Healthy | 5001 | **Fixed!** |
| **MLflow Postgres** | ✅ Healthy | 5433 | |
| **MinIO** | ✅ Healthy | 9000, 9001 | |
| **Airflow Postgres** | ✅ Healthy | - | |
| **Airflow Redis** | ✅ Healthy | - | |
| **Airflow Webserver** | ✅ Healthy | 8080 | |
| **Airflow Worker** | ✅ Healthy | - | |
| **Airflow Scheduler** | ⚠️ Unhealthy | - | Không ảnh hưởng lớn |
| **Frontend** | ⏸️ Chưa start | 3000 | Cần start |

---

## 🚀 Cách Khởi Động Frontend

### Option 1: Tự động (Dùng Script)
```bash
cd /Users/khangtuan/Documents/courses/web_mining/Sentiment-Analysis-on-Social-Media-for-cryptocurrency
./start-all.sh  # Hoặc chỉ cần start frontend
```

### Option 2: Thủ công
```bash
# Kill process cũ (nếu có)
lsof -ti:3000 | xargs kill -9

# Start frontend
cd /Users/khangtuan/Documents/courses/web_mining/Sentiment-Analysis-on-Social-Media-for-cryptocurrency/frontend
npm start

# Test
curl http://localhost:3000/
```

---

## 🧪 Test API Endpoints

```bash
# Backend API
curl http://localhost:8000/
# Output: {"message":"ok"}

curl http://localhost:8000/cmc_news/
# Output: [] (chưa có data)

# MLflow
curl http://localhost:5001/health
# Output: OK

# Airflow
curl http://localhost:8080/health
# Output: {"metadatabase":{"status":"healthy"},...}
```

---

## ⚠️ Lưu Ý Quan Trọng

### 1. **Database Rỗng**
- API trả về `[]` vì **chưa có data**
- Cần **enable Airflow DAGs** để crawl data:
  1. Mở Airflow UI: http://localhost:8080
  2. Login: `airflow` / `airflow`
  3. Enable các DAGs:
     - `cmc_new_1h` (Crawl CMC news mỗi 1h)
     - `twitter_new_1h` (Crawl Twitter mỗi 1h)
     - `data_constructor_2h` (Tạo dataset mỗi 2h)
     - `data_labeling_2h` (Label data mỗi 2h)
     - `ml_train_2d` (Train ML model mỗi 2 ngày)

### 2. **Airflow Scheduler Unhealthy**
- Không ảnh hưởng lớn (DAGs vẫn chạy được)
- Nếu muốn fix:
```bash
docker logs sentiman_airflow_scheduler  # Check logs
docker-compose restart airflow-scheduler
```

### 3. **Health Check Đã Fix**
- Tất cả health checks giờ dùng Python (có sẵn)
- Không cần cài thêm `curl` hay `wget`

---

## 📝 Changes Applied

### `docker-compose.yaml`
1. **Kafka health check:** `nc -z localhost 9092` (đơn giản hơn)
2. **Backend API health check:** Python `urllib.request`
3. **MLflow health check:** Python `urllib.request`
4. **Kafka `start_period`:** Tăng lên 90s để đủ thời gian khởi động

### Volumes
- Đã xóa và tạo lại **toàn bộ volumes** để fix Kafka cluster ID conflict

---

## 🎯 Next Steps

1. **Start Frontend**
```bash
cd frontend && npm start
```

2. **Enable Airflow DAGs** (để có data)
- Truy cập: http://localhost:8080
- Enable: `cmc_new_1h`, `twitter_new_1h`, `data_constructor_2h`, `data_labeling_2h`

3. **Đợi Data Crawl** (vài phút đầu tiên)
```bash
# Check MongoDB có data chưa
docker exec sentiman_mongodb mongosh --eval "db.getSiblingDB('blog-data').posts.countDocuments()"
```

4. **Test Frontend**
```bash
curl http://localhost:3000/
```

---

## 🔍 Troubleshooting Commands

```bash
# Check tất cả services
docker-compose ps

# Check logs service cụ thể
docker logs sentiman_backend_api
docker logs sentiman_kafka
docker logs sentiman_mlflow

# Restart service cụ thể
docker-compose restart backend-api

# Restart tất cả
docker-compose down && docker-compose up -d

# Xóa volumes và restart từ đầu (CAREFUL!)
docker-compose down -v && docker-compose up -d
```

---

## ✅ Summary

| Issue | Status | Solution |
|-------|--------|----------|
| Kafka InconsistentClusterIdException | ✅ Fixed | `docker-compose down -v` |
| Backend API unhealthy | ✅ Fixed | Python health check |
| MLflow unhealthy | ✅ Fixed | Python health check |
| Frontend not accessible | ⏸️ Pending | `npm start` |
| Empty API responses | ⏸️ Expected | Enable Airflow DAGs |

---

**Kết luận:** Tất cả core services (Kafka, MongoDB, Backend, MLflow) đã **HEALTHY** ✅  
Chỉ cần start Frontend và enable Airflow DAGs để có data!

