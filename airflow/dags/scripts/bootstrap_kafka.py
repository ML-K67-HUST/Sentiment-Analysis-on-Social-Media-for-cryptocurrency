"""
Manual script to push existing articles to Kafka
Run this to bootstrap the pipeline with existing data
"""

import sys
sys.path.append('/opt/airflow/dags')

from database.kafka import Kafka
from database.mongodb import MongoManager
from utils.common import get_chunks
from crawler.coinmarketcap import CMC_NEWS_KAFKA_TOPIC

def push_existing_articles_to_kafka(limit=100):
    """
    Push existing articles from MongoDB to Kafka
    This bootstraps the consumer pipeline
    """
    mongo = MongoManager('blog-data')
    kafka = Kafka()
    
    # Get latest articles without sentiment
    print(f"🔍 Finding articles without sentiment processing...")
    
    # Get all article hash_ids
    articles = list(mongo.find(
        collection_name='cmc_news',
        filter={},
        sort=('crawled_at', -1),
        limit=limit
    ))
    
    if not articles:
        print("❌ No articles found in cmc_news")
        return
    
    hash_ids = [art['hash_id'] for art in articles if 'hash_id' in art]
    
    print(f"✅ Found {len(hash_ids)} articles")
    print(f"📤 Pushing to Kafka topic: {CMC_NEWS_KAFKA_TOPIC}")
    
    # Chunk and send
    chunk_hash_ids = get_chunks(hash_ids, 10)
    
    total_sent = 0
    for chunk in chunk_hash_ids:
        message = {"hash_ids": chunk}
        kafka.producer_send(CMC_NEWS_KAFKA_TOPIC, message)
        total_sent += len(chunk)
        print(f"  ✓ Pushed {len(chunk)} articles (total: {total_sent})")
    
    print(f"\n🎉 Successfully pushed {total_sent} articles to Kafka!")
    print(f"   Consumers will now process these articles")

if __name__ == "__main__":
    push_existing_articles_to_kafka(limit=100)
