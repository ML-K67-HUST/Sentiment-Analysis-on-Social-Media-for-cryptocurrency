# Makefile for Docker Compose Management

.PHONY: help up down restart logs build clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make up           - Start all services"
	@echo "  make up-base      - Start only base infrastructure (MongoDB, Kafka)"
	@echo "  make up-ml        - Start MLflow stack"
	@echo "  make up-airflow   - Start Airflow stack"
	@echo "  make up-backend   - Start backend services"
	@echo "  make down         - Stop all services (keep volumes)"
	@echo "  make down-clean   - Stop all services and remove volumes"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - View logs from all services"
	@echo "  make build        - Rebuild all images"
	@echo "  make ps           - Show running containers"

# Start all services
up:
	docker-compose -f docker-compose.base.yml \
		-f docker-compose.mlflow.yml \
		-f docker-compose.airflow.yml \
		-f docker-compose.backend.yml \
		up -d

# Start only base infrastructure
up-base:
	docker-compose -f docker-compose.base.yml up -d

# Start MLflow
up-ml:
	docker-compose -f docker-compose.base.yml -f docker-compose.mlflow.yml up -d

# Start Airflow
up-airflow:
	docker-compose -f docker-compose.base.yml -f docker-compose.airflow.yml up -d

# Start backend services
up-backend:
	docker-compose -f docker-compose.base.yml -f docker-compose.backend.yml up -d

# Start monitoring stack (Kafka UI + Grafana)
up-monitoring:
	docker-compose -f docker-compose.base.yml -f docker-compose.monitoring.yml up -d

# Stop all services (keep volumes)
down:
	docker-compose -f docker-compose.base.yml \
		-f docker-compose.mlflow.yml \
		-f docker-compose.airflow.yml \
		-f docker-compose.backend.yml \
		down

# Stop all and remove volumes
down-clean:
	docker-compose -f docker-compose.base.yml \
		-f docker-compose.mlflow.yml \
		-f docker-compose.airflow.yml \
		-f docker-compose.backend.yml \
		down -v

# Restart all services
restart:
	$(MAKE) down
	$(MAKE) up

# View logs
logs:
	docker-compose -f docker-compose.base.yml \
		-f docker-compose.mlflow.yml \
		-f docker-compose.airflow.yml \
		-f docker-compose.backend.yml \
		logs -f

# Rebuild images
build:
	docker-compose -f docker-compose.base.yml \
		-f docker-compose.mlflow.yml \
		-f docker-compose.airflow.yml \
		-f docker-compose.backend.yml \
		build

# Show running containers
ps:
	docker-compose -f docker-compose.base.yml \
		-f docker-compose.mlflow.yml \
		-f docker-compose.airflow.yml \
		-f docker-compose.backend.yml \
		ps
