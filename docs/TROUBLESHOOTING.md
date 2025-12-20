# 🔧 Troubleshooting Guide

Common issues and their solutions for the Cryptocurrency Sentiment Analysis system.

## Table of Contents

1. [Docker Issues](#docker-issues)
2. [Kafka Issues](#kafka-issues)
3. [MongoDB Issues](#mongodb-issues)
4. [Airflow Issues](#airflow-issues)
5. [Backend API Issues](#backend-api-issues)
6. [Frontend Issues](#frontend-issues)
7. [Network Issues](#network-issues)
8. [Performance Issues](#performance-issues)

---

## Docker Issues

### Issue: Docker daemon not running

**Symptoms:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solution:**
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker

# Windows
# Start Docker Desktop from Start Menu
```

---

### Issue: Insufficient Docker resources

**Symptoms:**
- Services randomly crash
- Out of memory errors
- Slow performance

**Solution:**

Open Docker Desktop → Settings → Resources:
- **CPU**: Minimum 4 cores (recommended: 6+)
- **Memory**: Minimum 8 GB (recommended: 12+ GB)
- **Disk**: Minimum 50 GB free space

---

### Issue: Port conflicts

**Symptoms:**
```
Error: bind: address already in use
```

**Solution:**

Check what's using the port:
```bash
# macOS/Linux
lsof -i :8080  # Replace 8080 with your port
kill -9 <PID>

# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

Or change the port in `docker-compose.yaml`:
```yaml
ports:
  - "8081:8080"  # Changed from 8080:8080
```

---

## Kafka Issues

### Issue: Kafka connection refused (localhost:9092)

**Symptoms:**
```
KafkaConnectionError: 111 ECONNREFUSED
Node 1 connection failed -- refreshing metadata
```

**Root Cause:**
Kafka is advertising `localhost:9092` in metadata, but Docker services need to connect via `kafka:9092`.

**Solution:**

1. **Clean restart with volume removal:**
```bash
docker-compose down -v
docker-compose up -d
```

2. **Verify Kafka config** in `docker-compose.yaml`:
```yaml
KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka:9092,EXTERNAL://localhost:9093
KAFKA_LISTENERS: INTERNAL://0.0.0.0:9092,EXTERNAL://0.0.0.0:9093
KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT
KAFKA_INTER_BROKER_LISTENER_NAME: INTERNAL
```

3. **Test connectivity** from Airflow:
```bash
docker exec sentiman_airflow_worker nc -zv kafka 9092
```

**Prevention:**
Always use `docker-compose down -v` (with `-v` flag) when restarting Kafka to remove old data.

---

### Issue: Kafka InconsistentClusterIdException

**Symptoms:**
```
InconsistentClusterIdException: The Cluster ID doesn't match stored
```

**Root Cause:**
Old Kafka data from a previous cluster is conflicting with a new Zookeeper cluster ID.

**Solution:**
```bash
# Stop everything and remove volumes
docker-compose down -v

# Remove Kafka volume specifically
docker volume rm sentiman_kafka_data

# Restart
docker-compose up -d
```

---

### Issue: Kafka topics not created

**Symptoms:**
- Messages not being produced/consumed
- Topic does not exist error

**Solution:**

1. **Check if topics exist:**
```bash
docker exec sentiman_kafka kafka-topics --bootstrap-server kafka:9092 --list
```

2. **Create topics manually:**
```bash
docker exec sentiman_kafka kafka-topics \
  --bootstrap-server kafka:9092 \
  --create \
  --topic coinmarketcap-news \
  --partitions 3 \
  --replication-factor 1
```

3. **Enable auto-create** in `docker-compose.yaml`:
```yaml
KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
```

---

## MongoDB Issues

### Issue: MongoDB connection refused

**Symptoms:**
```
localhost:27017: [Errno 111] Connection refused
```

**Root Cause:**
Backend is trying to connect to `localhost:27017` instead of `mongodb:27017`.

**Solution:**

1. **Check `.env` file:**
```bash
# Should be:
MONGODB_CONNECTION_STRING=mongodb://mongodb:27017

# NOT:
MONGODB_CONNECTION_STRING=mongodb://localhost:27017
```

2. **Rebuild backend:**
```bash
docker-compose up -d --build backend-api
```

3. **Test connection:**
```bash
docker exec sentiman_backend_api python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://mongodb:27017')
print(client.list_database_names())
"
```

---

### Issue: MongoDB healthcheck failing

**Symptoms:**
```
sentiman_mongodb    Up (unhealthy)
```

**Solution:**

1. **Check MongoDB logs:**
```bash
docker logs sentiman_mongodb --tail 50
```

2. **Test health check command:**
```bash
docker exec sentiman_mongodb mongosh --eval "db.adminCommand('ping')"
```

3. **Increase health check timeout** in `docker-compose.yaml`:
```yaml
healthcheck:
  test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
  interval: 10s
  timeout: 10s    # Increased from 5s
  retries: 20
  start_period: 40s
```

---

## Airflow Issues

### Issue: Airflow webserver not accessible

**Symptoms:**
- Cannot access http://localhost:8080
- Connection timeout or refused

**Solution:**

1. **Check if webserver is running:**
```bash
docker-compose ps | grep airflow_webserver
```

2. **Check webserver logs:**
```bash
docker logs sentiman_airflow_webserver --tail 50
```

3. **Wait for initialization:**
Airflow can take 2-3 minutes to fully start. Check health:
```bash
docker inspect sentiman_airflow_webserver --format='{{json .State.Health}}' | jq .
```

4. **Restart webserver:**
```bash
docker-compose restart airflow-webserver
```

---

### Issue: DAG import errors

**Symptoms:**
- DAGs not showing in Airflow UI
- Import errors in logs

**Solution:**

1. **Check DAG syntax:**
```bash
docker exec sentiman_airflow_webserver airflow dags list
```

2. **View DAG errors:**
```bash
docker exec sentiman_airflow_webserver airflow dags list-import-errors
```

3. **Fix Python path:**
```bash
docker exec sentiman_airflow_webserver python -c "import sys; print('\n'.join(sys.path))"
```

4. **Restart scheduler:**
```bash
docker-compose restart airflow-scheduler
```

---

### Issue: Tasks stuck in "running" state

**Symptoms:**
- Tasks never complete
- Zombie tasks in Airflow UI

**Solution:**

1. **Check worker logs:**
```bash
docker logs sentiman_airflow_worker -f
```

2. **Clear task state:**
```bash
docker exec sentiman_airflow_webserver airflow tasks clear <dag_id> <task_id>
```

3. **Restart worker:**
```bash
docker-compose restart airflow-worker
```

---

## Backend API Issues

### Issue: Backend API not responding

**Symptoms:**
```
curl: (7) Failed to connect to localhost port 8000
```

**Solution:**

1. **Check if container is running:**
```bash
docker-compose ps | grep backend_api
```

2. **Check API logs:**
```bash
docker logs sentiman_backend_api --tail 50
```

3. **Check health endpoint:**
```bash
curl http://localhost:8000/health
```

4. **Restart API:**
```bash
docker-compose restart backend-api
```

---

### Issue: LLM API errors

**Symptoms:**
```
LLM_PROVIDER_ERROR: Failed to connect to Gemini API
```

**Solution:**

1. **Verify API key** in `.env`:
```bash
grep GEMINI_API_KEY .env
```

2. **Test API key manually:**
```bash
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_KEY"
```

3. **Check rate limits:**
- Gemini Free: 15 requests/minute
- Wait 1 minute and retry

4. **Switch provider** in `.env`:
```bash
LLM_PROVIDER=together  # If you have Together AI key
```

---

## Frontend Issues

### Issue: Frontend not accessible (port 3000)

**Symptoms:**
- Cannot access http://localhost:3000
- ERR_CONNECTION_REFUSED

**Solution:**

1. **Check if frontend is running:**
```bash
ps aux | grep "node server.js"
```

2. **Check logs:**
```bash
tail -f logs/frontend.log
```

3. **Restart frontend:**
```bash
cd frontend
node server.js > ../logs/frontend.log 2>&1 &
```

4. **Check port availability:**
```bash
lsof -i :3000
```

---

### Issue: Data not loading in frontend

**Symptoms:**
- Empty charts
- "No data available" messages

**Solution:**

1. **Check backend connectivity:**
```bash
curl http://localhost:8000/chart/?symbol=BTC
```

2. **Check browser console** (F12):
- Look for CORS errors
- Check network requests

3. **Verify data in MongoDB:**
```bash
docker exec sentiman_mongodb mongosh --eval "
  use twitter_crawler
  db.coinmarketcap_news.countDocuments()
"
```

4. **Trigger DAG** to collect data:
```bash
docker exec sentiman_airflow_webserver airflow dags trigger cmc_news_24h
```

---

## Network Issues

### Issue: Services cannot communicate

**Symptoms:**
```
getaddrinfo ENOTFOUND kafka
Connection refused to mongodb:27017
```

**Solution:**

1. **Check Docker network:**
```bash
docker network ls | grep sentiman
docker network inspect sentiman-net
```

2. **Verify all services in same network:**
```bash
docker inspect sentiman_kafka | grep sentiman-net
docker inspect sentiman_mongodb | grep sentiman-net
```

3. **Test connectivity:**
```bash
docker exec sentiman_airflow_worker ping kafka -c 3
docker exec sentiman_backend_api ping mongodb -c 3
```

4. **Recreate network:**
```bash
docker-compose down
docker network rm sentiman-net
docker-compose up -d
```

---

## Performance Issues

### Issue: Slow data processing

**Symptoms:**
- Tasks taking too long
- High CPU/memory usage

**Solution:**

1. **Check resource usage:**
```bash
docker stats
```

2. **Increase worker concurrency** in `docker-compose.yaml`:
```yaml
AIRFLOW__CELERY__WORKER_CONCURRENCY: 8  # Increase from 4
```

3. **Optimize Kafka partitions:**
```bash
docker exec sentiman_kafka kafka-topics \
  --bootstrap-server kafka:9092 \
  --alter \
  --topic coinmarketcap-news \
  --partitions 6  # Increase partitions
```

4. **Tune MongoDB indexes:**
```bash
docker exec sentiman_mongodb mongosh --eval "
  use twitter_crawler
  db.coinmarketcap_news.createIndex({ 'crypto_symbols': 1, 'published_at': -1 })
"
```

---

## General Debugging Commands

### View all service logs
```bash
docker-compose logs -f --tail=100
```

### Check specific service
```bash
docker logs sentiman_<service_name> -f
```

### Enter container shell
```bash
docker exec -it sentiman_<service_name> bash
```

### Check service health
```bash
docker-compose ps
docker inspect sentiman_<service_name> --format='{{json .State.Health}}' | jq .
```

### Complete reset
```bash
# Nuclear option: remove everything
docker-compose down -v
docker system prune -a --volumes
docker-compose up -d
```

---

## Getting Help

If you still have issues:

1. **Check logs** with increased verbosity
2. **Search existing issues** on GitHub
3. **Open a new issue** with:
   - System info (OS, Docker version)
   - Error logs (full output)
   - Steps to reproduce
   - Expected vs actual behavior

---

## Useful Resources

- [Docker Documentation](https://docs.docker.com/)
- [Apache Airflow Troubleshooting](https://airflow.apache.org/docs/apache-airflow/stable/troubleshooting.html)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [MongoDB Troubleshooting](https://www.mongodb.com/docs/manual/tutorial/)

