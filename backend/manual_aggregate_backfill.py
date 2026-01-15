"""
Manual Backfill Aggregation Script
Aggregates ANY 10-min window that has articles but no aggregation record.
Also fetches historical BTC price for labeling.
"""
import time
from datetime import datetime, timedelta
import numpy as np
import requests
import json
import sys
import os

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.mongodb import MongoManager
from config import config

def weighted_average(values, weights):
    if not values or not weights or sum(weights) == 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights)) / sum(weights)

def get_bitcoin_price_at_timestamp(timestamp):
    # Using CoinRanking API for historical
    headers = {
        'x-access-token': 'coinranking20b7cf109bbe9e42388a3faf8fe62f8ddda36dd7ec8a9f1f',
    }
    # Using simple retry logic
    for _ in range(3):
        try:
            response = requests.get(
                f"https://api.coinranking.com/v2/coin/Qwsogvtv82FCd/price?timestamp={timestamp}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.text
        except Exception:
            time.sleep(1)
    return None

def manual_backfill():
    print("🚀 Starting Manual Aggregation Backfill...")
    
    # Initialize MongoDB
    conn_str = config.MONGODB_CONNECTION_STRING
    if "@mongodb" in conn_str:
        conn_str = conn_str.replace("@mongodb", "@localhost")
    mongo_client = MongoManager('blog-data', uri=conn_str)
    
    # 1. Identify all 10-min windows from RECENT articles
    print("🔍 Identifying relevant time windows...")
    
    articles = list(mongo_client.find('article_features', limit=1000, sort=('timestamp', -1)))
    
    if not articles:
        print("No articles with features found.")
        return

    windows_to_process = set()
    
    for a in articles:
        # Use 'crawled_at' OR 'timestamp'
        # The standard aggregator uses 'crawled_at'. Let's stick to that if available.
        ts = a.get('crawled_at') or a.get('timestamp')
        if not ts:
            continue
            
        dt = datetime.fromtimestamp(ts)
        # Round down to nearest 10 min
        minute = (dt.minute // 10) * 10
        window_start = dt.replace(minute=minute, second=0, microsecond=0)
        windows_to_process.add(int(window_start.timestamp()))

    sorted_windows = sorted(list(windows_to_process))
    print(f"   Found {len(sorted_windows)} potentially relevant windows.")
    
    processed_count = 0
    
    for window_start_ts in sorted_windows:
        window_end_ts = window_start_ts + 600
        window_dt = datetime.fromtimestamp(window_start_ts)
        
        # Check if exists
        existing = mongo_client.find_one(
            'aggregated_features_10min', 
            filter={'window_start': window_start_ts}
        )
        if existing and existing.get('aggregation_status') == 'complete':
            # Could re-aggregate if we want to include new manual data
            # Let's force update if 'num_articles' is low or just to be safe for manual runs
            pass

        print(f"\n⚙️  Processing Window: {window_dt}")
        
        # Find articles in range
        # Matches logic in aggregate_10min_features.py
        # Find articles with features in this range
        features_in_window = list(mongo_client.find(
            'article_features',
            filter={
                '$or': [
                    {'crawled_at': {'$gte': window_start_ts, '$lt': window_end_ts}},
                    {'timestamp': {'$gte': window_start_ts, '$lt': window_end_ts}} # Fallback
                ],
                'processing_status': 'nlp_done'
            }
        ))
        
        if not features_in_window:
            print("   No features found in this window.")
            continue
            
        hash_ids = [f['hash_id'] for f in features_in_window]
        
        # Get matching sentiments
        sentiments = list(mongo_client.find(
            'cmc_sentiment_data',
            filter={'hash_id': {'$in': hash_ids}}
        ))
        
        sentiment_map = {s['hash_id']: s for s in sentiments}
        
        complete_articles = []
        for f in features_in_window:
            hid = f['hash_id']
            if hid in sentiment_map:
                complete_articles.append({
                    'hash_id': hid,
                    'nlp': f,
                    'llm': sentiment_map[hid]
                })
        
        if not complete_articles:
            print("   No complete articles (NLP+LLM) found.")
            continue
            
        print(f"   Found {len(complete_articles)} complete articles.")
        
        # Aggregation Logic
        sentiment_scores = [a['llm']['sentiment_score'] for a in complete_articles]
        confidences = [a['llm']['confidence'] for a in complete_articles]
        
        llm_sentiment_avg = weighted_average(sentiment_scores, confidences)
        llm_confidence_avg = np.mean(confidences)
        
        nlp_features_agg = {}
        feature_keys = list(complete_articles[0]['nlp']['nlp_features'].keys())
        
        for key in feature_keys:
            values = [a['nlp']['nlp_features'][key] for a in complete_articles]
            if 'ratio' in key or 'score' in key:
                nlp_features_agg[f'avg_{key}'] = weighted_average(values, confidences)
            elif 'count' in key or 'word_count' in key or 'length' in key:
                nlp_features_agg[f'total_{key}'] = sum(values)
            else:
                nlp_features_agg[f'avg_{key}'] = np.mean(values)
                
        # Labeling (Get Price Movement)
        start_ts_str = str(int(window_start_ts))
        end_ts_str = str(int(window_end_ts))
        
        label_data = {}
        try:
            p1_res = get_bitcoin_price_at_timestamp(start_ts_str)
            p2_res = get_bitcoin_price_at_timestamp(end_ts_str)
            
            if p1_res and p2_res:
                p1 = float(json.loads(p1_res)['data']['price'])
                p2 = float(json.loads(p2_res)['data']['price'])
                movement = ((p2 - p1) / p1) * 100
                label_data = {
                    'labeled': True,
                    'price_movement_10min': movement,
                    'labeled_at': datetime.utcnow().timestamp(),
                    'btc_price': p1
                }
                print(f"   ✅ Labeled: {movement:+.4f}%")
            else:
                print("   ⚠️  Failed to fetch price history.")
                label_data = {'labeled': False, 'btc_price': 0.0}
        except Exception as e:
            print(f"   ⚠️  Labeling error: {e}")
            label_data = {'labeled': False, 'btc_price': 0.0}
            
        # Save
        aggregated = {
            'window_start': window_start_ts,
            'window_end': window_end_ts,
            'window_datetime': window_dt.isoformat(),
            'num_articles': len(complete_articles),
            'llm_sentiment_avg': round(llm_sentiment_avg, 4),
            'llm_confidence_avg': round(llm_confidence_avg, 4),
            'nlp_features_agg': {k: round(v, 4) if isinstance(v, float) else v 
                                for k, v in nlp_features_agg.items()},
            'aggregation_status': 'complete',
            'aggregated_at': int(datetime.utcnow().timestamp()),
            **label_data
        }
        
        mongo_client.update_one(
            'aggregated_features_10min',
            {'window_start': window_start_ts},
            {'$set': aggregated},
            upsert=True
        )
        processed_count += 1
        
    print(f"\n✅ Backfill Complete. Processed {processed_count} windows.")

if __name__ == "__main__":
    manual_backfill()
