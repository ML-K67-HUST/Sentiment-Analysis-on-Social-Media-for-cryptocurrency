#!/usr/bin/env python3
"""
Check if articles in current 30-min window have NLP features
"""
import sys
sys.path.append('/opt/airflow/dags')

from database.mongodb import MongoManager
from database.kafka import Kafka
from utils.common import get_chunks
from crawler.coinmarketcap import CMC_NEWS_KAFKA_TOPIC
from datetime import datetime, timedelta

def check_and_push_window_articles():
    mongo = MongoManager('blog-data')
    
    # Calculate time window (same as aggregate DAG)
    now = datetime.utcnow()
    if now.minute < 30:
        window_start = now.replace(minute=0, second=0, microsecond=0)
    else:
        window_start = now.replace(minute=30, second=0, microsecond=0)
    window_end = window_start + timedelta(minutes=30)
    window_start = window_start - timedelta(minutes=30)
    
    window_start_ts = int(window_start.timestamp())
    window_end_ts = int(window_end.timestamp())
    
    print(f'\n{"="*80}')
    print(f'🔍 CHECKING WINDOW ARTICLES')
    print(f'{"="*80}')
    print(f'Window: {window_start} - {window_end}')
    print(f'Timestamps: {window_start_ts} - {window_end_ts}\n')
    
    # Find BTC articles in window (only process BTC to save LLM API costs)
    articles = list(mongo.find(
        collection_name='cmc_news',
        filter={
            'crawled_at': {'$gte': window_start_ts, '$lt': window_end_ts},
            'symbol': 'BTC'  # Only process BTC articles
        }
    ))
    
    print(f'✅ Found {len(articles)} BTC articles crawled in window')
    
    if not articles:
        print('❌ No articles in window')
        return
    
    hash_ids = [a['hash_id'] for a in articles]
    print(f'   First 5 hash_ids: {hash_ids[:5]}\n')
    
    # Check which ones have NLP features
    features = list(mongo.find(
        collection_name='article_features',
        filter={
            'hash_id': {'$in': hash_ids},
            'processing_status': 'nlp_done'
        }
    ))
    
    feature_hash_ids = set([f['hash_id'] for f in features])
    missing_hash_ids = [h for h in hash_ids if h not in feature_hash_ids]
    
    print(f'📊 NLP Features Status:')
    print(f'   ✅ With NLP features: {len(features)}')
    print(f'   ❌ Missing NLP features: {len(missing_hash_ids)}')
    
    if missing_hash_ids:
        print(f'\n📤 Pushing {len(missing_hash_ids)} articles to Kafka...')
        kafka = Kafka()
        chunk_hash_ids = get_chunks(missing_hash_ids, 10)
        
        total_sent = 0
        for chunk in chunk_hash_ids:
            message = {"hash_ids": chunk}
            kafka.producer_send(CMC_NEWS_KAFKA_TOPIC, message)
            total_sent += len(chunk)
            print(f'  ✓ Pushed {len(chunk)} articles (total: {total_sent})')
        
        print(f'\n🎉 Successfully pushed {total_sent} articles to Kafka!')
        print(f'   Wait 1-2 minutes for NLP consumer to process them')
    else:
        print(f'\n✅ All articles already have NLP features!')
    
    print(f'\n{"="*80}\n')

if __name__ == "__main__":
    check_and_push_window_articles()

