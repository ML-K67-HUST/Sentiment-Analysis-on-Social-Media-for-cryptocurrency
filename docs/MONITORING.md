# Monitoring Stack Setup Guide

## 🎯 Overview

Professional monitoring stack với:
- **Kafka UI** - Monitor Kafka topics, consumers, messages
- **Grafana** - Beautiful dashboards & visualizations  
- **Prometheus** - Metrics collection & storage
- **MongoDB Exporter** - MongoDB performance metrics

## 🚀 Quick Start

### 1. Start Monitoring Stack

```bash
# Start all monitoring services
docker-compose -f docker-compose.base.yml -f docker-compose.monitoring.yml up -d

# Or use Makefile
make up-monitoring
```

### 2. Access UIs

**Kafka UI:** http://localhost:8090
- Monitor topics, messages, consumer groups
- See consumer lag
- View message content

**Grafana:** http://localhost:3000  
- Username: `admin`
- Password: `admin` (change on first login)
- Pre-configured dashboards for consumers

**Prometheus:** http://localhost:9090
- Raw metrics queries
- Advanced monitoring

## 📊 Kafka UI Features

### Topics Monitoring
- ✅ See all topics (coinmarketcap-news, etc.)
- ✅ Message count per partition
- ✅ Message throughput

### Consumer Groups
- ✅ **Consumer lag** -얼마 messages chưa xử lý
- ✅ **Offset position** - đang ở đâu trong topic
- ✅ **Members** - số consumers đang chạy

### Messages
- ✅ View message content
- ✅ Filter by timestamp
- ✅ Search messages

### Example: Check LLM Consumer Status

1. Mở Kafka UI: http://localhost:8090
2. Click **Consumer Groups**
3. Tìm `llm-sentiment-group`
4. Xem:
   - **Lag**: Nếu > 100 → Consumer chậm
   - **Members**: Nếu = 0 → Consumer không chạy
   - **Offset**: Tăng → Consumer đang xử lý

## 📈 Grafana Dashboards

### Consumer Metrics Dashboard

**Panels:**
1. **Success Rate** (Gauge)
   - LLM Consumer: X%
   - NLP Consumer: Y%
   
2. **Articles Processed** (Graph over time)
   - Line chart showing throughput
   
3. **Errors** (Stat panel)
   - Total errors today
   - Alert if > threshold

4. **Processing Lag** (Graph)
   - Time between crawl and processing
   
5. **MongoDB Collections** (Bar chart)
   - Document counts per collection

### How to Create Custom Dashboard

1. Login to Grafana: http://localhost:3000
2. Click **+** → **Dashboard**
3. Add Panel
4. Select **Prometheus** datasource
5. Query examples:

```promql
# Consumer success rate
consumer_success_rate{consumer_name="LLM_Consumer"}

# Articles processed per minute
rate(consumer_processed_total[1m])

# MongoDB collection size
mongodb_collection_count{collection="cmc_news"}

# Error rate
rate(consumer_errors_total[5m])
```

6. Save dashboard

## 🔔 Alerting (Optional)

### Setup Email Alerts

1. Grafana → Configuration → Notification channels
2. Add Email channel
3. Create Alert Rules:
   - Consumer lag > 1000 messages
   - Error rate > 10 per minute
   - Consumer offline > 5 minutes

### Example Alert Query

```promql
# Alert when consumer lag > 1000
kafka_consumergroup_lag > 1000

# Alert when errors spike
rate(consumer_errors_total[5m]) > 0.1
```

## 🐛 Troubleshooting with Monitoring Stack

### Problem: LLM Sentiment không xuất hiện trong MongoDB

**Step 1: Check Kafka UI**
1. Topics → `coinmarketcap-news`
2. Có messages mới không?
3. Nếu không → Crawler issue

**Step 2: Check Consumer Group**
1. Consumer Groups → `llm-sentiment-group`
2. Members = 0? → Consumer stopped
3. Lag tăng? → Consumer chạy nhưng chậm
4. Lag = 0? → Consumer đã xử lý hết

**Step 3: Check Grafana**
1. Consumer Metrics dashboard
2. Xem error count
3. Xem last processed timestamp
4. Nếu errors cao → Check logs

**Step 4: Check Prometheus Metrics**
```promql
# See if consumer is processing
consumer_processed_total{consumer_name="LLM_Consumer"}

# Check error rate
consumer_errors_total{consumer_name="LLM_Consumer"}
```

### Problem: Consumer chạy nhưng không process

**Kafka UI Check:**
- Lag không giảm → Consumer stuck
- Offset không tăng → Consumer không consume

**Fix:**
```bash
# Restart consumer
docker restart sentiman_backend_consumerdock

# Check logs
docker logs sentiman_backend_consumerdock --tail 100
```

## 📊 Metrics Available

### Consumer Metrics (from `consumer_metrics` collection)

```
consumer_processed_total - Total articles processed
consumer_errors_total - Total errors
consumer_skipped_total - Total skipped
consumer_success_rate - Success rate %
consumer_uptime_seconds - Uptime in seconds
consumer_last_processed_timestamp - Last activity
```

### MongoDB Metrics (from MongoDB Exporter)

```
mongodb_collection_count - Document count per collection
mongodb_connections - Active connections
mongodb_memory - Memory usage
mongodb_network_bytes_total - Network I/O
```

### Kafka Metrics (from Kafka UI)

```
kafka_topic_partitions - Number of partitions
kafka_consumergroup_lag - Consumer lag
kafka_topic_messages_total - Total messages
```

## 🎨 Grafana Dashboard JSON (Import Ready)

Create file: `monitoring/grafana/dashboards/consumer_dashboard.json`

```json
{
  "dashboard": {
    "title": "Consumer Monitoring",
    "panels": [
      {
        "title": "Consumer Success Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "consumer_success_rate"
          }
        ]
      },
      {
        "title": "Articles Processed",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(consumer_processed_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## 📱 Mobile Access

Grafana supports mobile:
- Install **Grafana Mobile** app
- Login with http://YOUR_IP:3000
- View dashboards on phone

## 🔐 Security (Production)

### Change Default Passwords

```bash
# Update .env
GRAFANA_USER=your_username
GRAFANA_PASSWORD=strong_password

# Restart
docker-compose -f docker-compose.monitoring.yml restart grafana
```

### Enable HTTPS

Use reverse proxy (Nginx) với SSL certificate.

## 💡 Best Practices

1. **Check Kafka UI daily** - Consumer lag trends
2. **Set up alerts** - Email khi có issues
3. **Monitor Grafana dashboards** - Spot trends
4. **Export dashboards** - Backup configurations
5. **Review metrics weekly** - Optimize performance

## 🎯 Quick Links

- Kafka UI: http://localhost:8090
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Consumer Metrics: http://localhost:8003/metrics

## 📚 Further Reading

- [Kafka UI Docs](https://docs.kafka-ui.provectus.io/)
- [Grafana Docs](https://grafana.com/docs/)
- [Prometheus Query Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
