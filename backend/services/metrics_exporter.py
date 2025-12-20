"""
Metrics Exporter for Prometheus
Exports consumer metrics in Prometheus format
"""

from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from database.mongodb import MongoManager
import time

app = FastAPI()

mongo = MongoManager('blog-data')

# Define Prometheus metrics
consumer_processed_total = Counter(
    'consumer_processed_total',
    'Total number of articles processed',
    ['consumer_name']
)

consumer_errors_total = Counter(
    'consumer_errors_total', 
    'Total number of errors',
    ['consumer_name']
)

consumer_skipped_total = Counter(
    'consumer_skipped_total',
    'Total number of skipped articles',
    ['consumer_name']
)

consumer_success_rate = Gauge(
    'consumer_success_rate',
    'Consumer success rate percentage',
    ['consumer_name']
)

consumer_uptime_seconds = Gauge(
    'consumer_uptime_seconds',
    'Consumer uptime in seconds',
    ['consumer_name']
)

consumer_last_processed_timestamp = Gauge(
    'consumer_last_processed_timestamp',
    'Timestamp of last processed article',
    ['consumer_name']
)

# MongoDB collection counts
mongodb_collection_count = Gauge(
    'mongodb_collection_count',
    'Number of documents in MongoDB collection',
    ['collection']
)

# Processing time histogram
processing_duration_seconds = Histogram(
    'processing_duration_seconds',
    'Time spent processing articles',
    ['consumer_name']
)


@app.get("/metrics")
async def metrics():
    """Export metrics in Prometheus format"""
    
    # Update metrics from MongoDB
    try:
        # Get consumer metrics
        consumers = list(mongo.find(
            collection_name='consumer_metrics',
            filter={}
        ))
        
        for consumer in consumers:
            name = consumer['consumer_name']
            
            # Set counter values (Prometheus counters only increase)
            consumer_processed_total.labels(consumer_name=name)._value.set(
                consumer.get('total_processed', 0)
            )
            consumer_errors_total.labels(consumer_name=name)._value.set(
                consumer.get('total_errors', 0)
            )
            consumer_skipped_total.labels(consumer_name=name)._value.set(
                consumer.get('total_skipped', 0)
            )
            
            # Set gauge values
            total = consumer.get('total_processed', 0) + consumer.get('total_errors', 0)
            if total > 0:
                success_rate = (consumer.get('total_processed', 0) / total) * 100
                consumer_success_rate.labels(consumer_name=name).set(success_rate)
            
            if consumer.get('started_at'):
                uptime = int(time.time()) - consumer['started_at']
                consumer_uptime_seconds.labels(consumer_name=name).set(uptime)
            
            if consumer.get('last_processed_at'):
                consumer_last_processed_timestamp.labels(consumer_name=name).set(
                    consumer['last_processed_at']
                )
        
        # Update MongoDB collection counts
        collections = [
            'cmc_news',
            'cmc_sentiment_data',
            'article_features',
            'aggregated_features_30min'
        ]
        
        for collection in collections:
            count = mongo.count_documents(collection, {})
            mongodb_collection_count.labels(collection=collection).set(count)
    
    except Exception as e:
        print(f"Error updating metrics: {e}")
    
    # Generate Prometheus format
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
