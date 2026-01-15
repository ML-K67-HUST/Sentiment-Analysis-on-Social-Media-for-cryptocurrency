"""
Temporal Framework Aggregator (Proof-of-Concept)

Implements 3-period temporal structure:
- Observation Window: 30 minutes (collect news)
- Lag Period: 10 minutes (enforced gap)
- Prediction Window: 10 minutes (target period)

This ensures proper causal inference by separating feature collection from target measurement.
"""

import time
from datetime import datetime, timedelta
import numpy as np
import requests
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.mongodb import MongoManager
from config import config

# Constants
OBSERVATION_DURATION = 30 * 60  # 30 minutes in seconds
LAG_DURATION = 10 * 60          # 10 minutes in seconds
PREDICTION_DURATION = 10 * 60   # 10 minutes in seconds
WINDOW_ADVANCE = 10 * 60        # Advance by 10 min (67% overlap)

def weighted_average(values, weights):
    """Compute confidence-weighted average."""
    if not values or not weights or sum(weights) == 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights)) / sum(weights)

def get_bitcoin_price_at_timestamp(timestamp):
    """Fetch historical Bitcoin price via CoinRanking API."""
    headers = {
        'x-access-token': 'coinranking20b7cf109bbe9e42388a3faf8fe62f8ddda36dd7ec8a9f1f',
    }
    
    for attempt in range(3):
        try:
            response = requests.get(
                f"https://api.coinranking.com/v2/coin/Qwsogvtv82FCd/price?timestamp={timestamp}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = json.loads(response.text)
                return float(data['data']['price'])
        except Exception as e:
            print(f"   ⚠️  Price fetch attempt {attempt+1} failed: {e}")
            time.sleep(1)
    return None

def aggregate_temporal_window(mongo_client, obs_start_ts, test_mode=False):
    """
    Aggregate a single temporal window.
    
    Args:
        mongo_client: MongoDB connection
        obs_start_ts: Observation window start timestamp (Unix seconds)
        test_mode: If True, only log actions without saving
        
    Returns:
        dict: Aggregated window data or None if insufficient data
    """
    # Calculate time periods
    obs_end_ts = obs_start_ts + OBSERVATION_DURATION
    lag_end_ts = obs_end_ts + LAG_DURATION
    pred_end_ts = lag_end_ts + PREDICTION_DURATION
    
    obs_start_dt = datetime.fromtimestamp(obs_start_ts)
    
    if not test_mode:
        print(f"\n⚙️  Window: {obs_start_dt} UTC")
        print(f"   Observation: [{obs_start_dt}]-[{datetime.fromtimestamp(obs_end_ts)}]")
        print(f"   Lag: [{datetime.fromtimestamp(obs_end_ts)}]-[{datetime.fromtimestamp(lag_end_ts)}]")
        print(f"   Prediction: [{datetime.fromtimestamp(lag_end_ts)}]-[{datetime.fromtimestamp(pred_end_ts)}]")
    
    # Find articles in OBSERVATION window only
    features_in_obs = list(mongo_client.find(
        'article_features',
        filter={
            '$or': [
                {'crawled_at': {'$gte': obs_start_ts, '$lt': obs_end_ts}},
                {'timestamp': {'$gte': obs_start_ts, '$lt': obs_end_ts}}
            ],
            'processing_status': 'nlp_done'
        }
    ))
    
    if not features_in_obs:
        if not test_mode:
            print("   ❌ No articles in observation window")
        return None
    
    # Get sentiments
    hash_ids = [f['hash_id'] for f in features_in_obs]
    sentiments = list(mongo_client.find(
        'cmc_sentiment_data',
        filter={'hash_id': {'$in': hash_ids}}
    ))
    
    sentiment_map = {s['hash_id']: s for s in sentiments}
    
    # Match NLP + LLM
    complete_articles = []
    for f in features_in_obs:
        hid = f['hash_id']
        if hid in sentiment_map:
            # Verify article timestamp < obs_end (no look-ahead)
            article_ts = f.get('crawled_at') or f.get('timestamp')
            if article_ts and article_ts < obs_end_ts:
                complete_articles.append({
                    'hash_id': hid,
                    'nlp': f,
                    'llm': sentiment_map[hid],
                    'timestamp': article_ts
                })
    
    if not complete_articles:
        if not test_mode:
            print("  ❌ No complete articles (NLP+LLM)")
        return None
    
    if not test_mode:
        print(f"   ✅ Found {len(complete_articles)} complete articles")
    
    # Aggregate features
    sentiment_scores = [a['llm']['sentiment_score'] for a in complete_articles]
    confidences = [a['llm']['confidence'] for a in complete_articles]
    
    llm_sentiment_avg = weighted_average(sentiment_scores, confidences)
    llm_confidence_avg = np.mean(confidences)
    
    # Aggregate NLP features
    nlp_features_agg = {}
    if complete_articles and 'nlp_features' in complete_articles[0]['nlp']:
        feature_keys = list(complete_articles[0]['nlp']['nlp_features'].keys())
        
        for key in feature_keys:
            values = [a['nlp']['nlp_features'][key] for a in complete_articles]
            if 'ratio' in key or 'score' in key:
                nlp_features_agg[f'avg_{key}'] = weighted_average(values, confidences)
            elif 'count' in key or 'word_count' in key or 'length' in key:
                nlp_features_agg[f'total_{key}'] = sum(values)
            else:
                nlp_features_agg[f'avg_{key}'] = np.mean(values)
    
    # Compute TARGET from PREDICTION window [lag_end, pred_end]
    # This is THE CRITICAL CHANGE - price movement is 10 min AFTER lag
    price_start_ts = lag_end_ts    # Start of prediction window
    price_end_ts = pred_end_ts      # End of prediction window
    
    label_data = {}
    try:
        p_start = get_bitcoin_price_at_timestamp(str(int(price_start_ts)))
        p_end = get_bitcoin_price_at_timestamp(str(int(price_end_ts)))
        
        if p_start and p_end:
            movement = ((p_end - p_start) / p_start) * 100
            label_data = {
                'labeled': True,
                'price_movement_lagged': movement,  # New field name
                'price_start': p_start,
                'price_end': p_end,
                'price_fetch_start_ts': price_start_ts,
                'price_fetch_end_ts': price_end_ts,
                'labeled_at': int(datetime.utcnow().timestamp())
            }
            if not test_mode:
                print(f"   💰 Price: ${p_start:.2f} → ${p_end:.2f} ({movement:+.4f}%)")
        else:
            if not test_mode:
                print("   ⚠️  Failed to fetch price data")
            label_data = {'labeled': False}
    except Exception as e:
        if not test_mode:
            print(f"   ⚠️  Labeling error: {e}")
        label_data = {'labeled': False}
    
    # Construct result
    aggregated = {
        # Temporal structure
        'observation_window': {
            'start': obs_start_ts,
            'end': obs_end_ts,
            'duration': OBSERVATION_DURATION
        },
        'lag_window': {
            'start': obs_end_ts,
            'end': lag_end_ts,
            'duration': LAG_DURATION
        },
        'prediction_window': {
            'start': lag_end_ts,
            'end': pred_end_ts,
            'duration': PREDICTION_DURATION
        },
        
        # Legacy compatibility
        'window_start': obs_start_ts,
        'window_datetime': obs_start_dt.isoformat(),
        
        # Features
        'num_articles': len(complete_articles),
        'llm_sentiment_avg': round(llm_sentiment_avg, 4),
        'llm_confidence_avg': round(llm_confidence_avg, 4),
        'nlp_features_agg': {k: round(v, 4) if isinstance(v, float) else v 
                             for k, v in nlp_features_agg.items()},
        
        # Target (with proper lag)
        **label_data,
        
        # Metadata
        'temporal_framework': '3-period',
        'aggregation_status': 'complete',
        'aggregated_at': int(datetime.utcnow().timestamp())
    }
    
    return aggregated

def run_temporal_aggregation(limit=None, test_mode=False):
    """
    Run temporal aggregation on historical data.
    
    Args:
        limit: Max number of windows to process (None = all)
        test_mode: If True, don't save to database
    """
    print("="*70)
    print("🚀 TEMPORAL FRAMEWORK AGGREGATOR")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Observation Window: {OBSERVATION_DURATION//60} minutes")
    print(f"  Lag Period: {LAG_DURATION//60} minutes")
    print(f"  Prediction Window: {PREDICTION_DURATION//60} minutes")
    print(f"  Window Advance: {WINDOW_ADVANCE//60} minutes (overlap={1-WINDOW_ADVANCE/OBSERVATION_DURATION:.0%})")
    
    if test_mode:
        print(f"\n⚠️  TEST MODE: No database writes")
    
   # Initialize MongoDB
    conn_str = config.MONGODB_CONNECTION_STRING
    if "@mongodb" in conn_str:
        conn_str = conn_str.replace("@mongodb", "@localhost")
    mongo_client = MongoManager('blog-data', uri=conn_str)
    
    # Get article time range
    oldest = mongo_client.find_one('article_features', sort=('timestamp', 1))
    newest = mongo_client.find_one('article_features', sort=('timestamp', -1))
    
    if not oldest or not newest:
        print("\n❌ No articles found")
        return
    
    start_ts = oldest.get('timestamp') or oldest.get('crawled_at')
    end_ts = newest.get('timestamp') or newest.get('crawled_at')
    
    print(f"\nData Range:")
    print(f"  Start: {datetime.fromtimestamp(start_ts)}")
    print(f"  End: {datetime.fromtimestamp(end_ts)}")
    
    # Generate observation windows
    # Start from first possible full observation window
    current_obs_start = start_ts
    # End when prediction window would exceed data range
    max_obs_start = end_ts - OBSERVATION_DURATION - LAG_DURATION - PREDICTION_DURATION
    
    windows_to_process = []
    while current_obs_start <= max_obs_start:
        windows_to_process.append(current_obs_start)
        current_obs_start += WINDOW_ADVANCE
    
    print(f"\nGenerated {len(windows_to_process)} potential windows")
    
    if limit:
        windows_to_process = windows_to_process[:limit]
        print(f"  (Limited to first {limit} for testing)")
    
    # Process windows
    successful = 0
    failed = 0
    
    for obs_start_ts in windows_to_process:
        result = aggregate_temporal_window(mongo_client, obs_start_ts, test_mode)
        
        if result:
            if not test_mode:
                # Save to new collection
                mongo_client.update_one(
                    'aggregated_features_temporal',
                    {'window_start': obs_start_ts},
                    {'$set': result},
                    upsert=True
                )
            successful += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "="*70)
    print("📊 AGGREGATION COMPLETE")
    print("="*70)
    print(f"  Successful: {successful}")
    print(f"  Failed (no data): {failed}")
    print(f"  Total: {len(windows_to_process)}")
    
    if not test_mode and successful > 0:
        print(f"\n✅ Data saved to collection: 'aggregated_features_temporal'")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Temporal Framework Aggregator')
    parser.add_argument('--limit', type=int, default=None, 
                        help='Limit number of windows to process')
    parser.add_argument('--test', action='store_true',
                        help='Test mode (no database writes)')
    
    args = parser.parse_args()
    
    run_temporal_aggregation(limit=args.limit, test_mode=args.test)
