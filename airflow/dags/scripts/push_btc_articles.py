#!/usr/bin/env python3
"""
Push BTC articles from current window to Kafka for LLM processing
"""
import sys
sys.path.append('/opt/airflow/dags')

from database.mongodb import MongoManager
from database.kafka import Kafka
from utils.common import get_chunks
from crawler.coinmarketcap import CMC_NEWS_KAFKA_TOPIC
from datetime import datetime, timedelta

def push_btc_window_articles():
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
    print(f'📤 PUSHING BTC ARTICLES TO KAFKA')
    print(f'{"="*80}')
    print(f'Window: {window_start} - {window_end}')
    print(f'Timestamps: {window_start_ts} - {window_end_ts}\n')
    
    # Find BTC articles in window from cmc_news
    btc_articles = list(mongo.find(
        collection_name='cmc_news',
        filter={
            'crawled_at': {'$gte': window_start_ts, '$lt': window_end_ts},
            'symbol': 'BTC'
        }
    ))
    
    if not btc_articles:
        print('❌ No BTC articles found')
        return
    
    btc_hash_ids = [a['hash_id'] for a in btc_articles]
    print(f'✅ Found {len(btc_hash_ids)} BTC articles with NLP features')
    print(f'   Hash IDs: {btc_hash_ids[:5]}\n')
    
    # Check which ones already have LLM sentiment
    sentiments = list(mongo.find(
        collection_name='cmc_sentiment_data',
        filter={'hash_id': {'$in': btc_hash_ids}}
    ))
    
    sentiment_hash_ids = set([s['hash_id'] for s in sentiments])
    missing_hash_ids = [h for h in btc_hash_ids if h not in sentiment_hash_ids]
    
    print(f'📊 LLM Sentiment Status:')
    print(f'   ✅ Already has LLM: {len(sentiments)}')
    print(f'   ❌ Missing LLM: {len(missing_hash_ids)}')
    
    if missing_hash_ids:
        print(f'\n📤 Pushing {len(missing_hash_ids)} BTC articles to Kafka...')
        kafka = Kafka()
        chunk_hash_ids = get_chunks(missing_hash_ids, 10)
        
        total_sent = 0
        for chunk in chunk_hash_ids:
            message = {"hash_ids": chunk}
            kafka.producer_send(CMC_NEWS_KAFKA_TOPIC, message)
            total_sent += len(chunk)
            print(f'  ✓ Pushed {len(chunk)} articles (total: {total_sent})')
        
        print(f'\n🎉 Successfully pushed {total_sent} BTC articles to Kafka!')
        print(f'   LLM consumer will process them (~20s per article)')
        print(f'   Estimated time: {total_sent * 20 // 60} minutes')
    else:
        print(f'\n✅ All BTC articles already have LLM sentiments!')
    
    print(f'\n{"="*80}\n')

if __name__ == "__main__":
    push_btc_window_articles()

