# Docker Compose Architecture

Đã tách docker-compose thành 4 files riêng biệt cho dễ quản lý:

## 📁 File Structure

```
docker-compose.base.yml      # Base infrastructure (MongoDB, Kafka, Zookeeper)
docker-compose.mlflow.yml    # MLflow stack (Postgres, MinIO, MLflow)
docker-compose.airflow.yml   # Airflow stack (Postgres, Redis, Airflow)
docker-compose.backend.yml   # Backend services (API, Consumers, ML API)
```

## 🚀 Usage

### Khởi động toàn bộ hệ thống:
```bash
make up
```

### Khởi động từng phần:
```bash
# Chỉ base infrastructure
make up-base

# Thêm MLflow
make up-ml

# Thêm Airflow
make up-airflow

# Thêm backend services
make up-backend
```

### Tắt services:
```bash
# Tắt nhưng giữ volumes (data không mất)
make down

# Tắt và xóa volumes (reset toàn bộ data)
make down-clean
```

### Các lệnh khác:
```bash
make logs      # Xem logs
make restart   # Restart tất cả
make build     # Rebuild images
make ps        # Xem containers đang chạy
```

## 🔧 Development Workflow

**Scenario 1: Chỉ test backend code**
```bash
make up-base              # Start MongoDB + Kafka
make up-backend           # Start backend services
```

**Scenario 2: Chỉ test ML training**
```bash
make up-base              # Start MongoDB + Kafka
make up-ml                # Start MLflow
make up-airflow           # Start Airflow (for DAGs)
```

**Scenario 3: Full system**
```bash
make up                   # Start everything
```

## 💡 Lợi ích

1. **Modular**: Bật/tắt từng phần riêng biệt
2. **Nhanh hơn**: Không cần rebuild/restart toàn bộ khi chỉ thay đổi 1 service
3. **Dễ debug**: Logs rõ ràng hơn khi chỉ chạy services cần thiết
4. **Tiết kiệm tài nguyên**: Chỉ chạy những gì cần

## ⚠️ Lưu ý

- **Volumes được share** giữa các file compose (định nghĩa trong base.yml)
- **Network được share** (sentiman-net)
- **Không cần xóa volumes** mỗi lần down, chỉ xóa khi:
  - Kafka/Zookeeper lỗi không khởi động được
  - Muốn reset toàn bộ data
  - Gặp conflict về schema MongoDB

## 🔄 Migration từ docker-compose.yaml cũ

File `docker-compose.yaml` cũ vẫn giữ nguyên để backward compatibility.

Để dùng cấu trúc mới:
```bash
# Tắt hệ thống cũ
docker-compose down

# Dùng Makefile mới
make up
```
