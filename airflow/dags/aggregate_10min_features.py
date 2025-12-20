"""
30-Minute Feature Aggregation DAG
Aggregates NLP features and LLM sentiment every 30 minutes
"""

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from database.mongodb import MongoManager
import numpy as np

DAG_NAME = "aggregate_10min_features"
TASK_AGGREGATE = "aggregate_features_10min"


def weighted_average(values, weights):
    """Calculate weighted average"""
    if not values or not weights or sum(weights) == 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights)) / sum(weights)


def aggregate_10min_features():
    """
    Aggregate features from all articles CRAWLED in the last 10 minutes
    
    Creates one aggregated record per 10-min window
    """
    mongo = MongoManager('blog-data')
    
    # Calculate 10-min window based on CURRENT TIME
    now = datetime.utcnow()
    # Round down to nearest 10 minutes
    minute = (now.minute // 10) * 10
    window_start = now.replace(minute=minute, second=0, microsecond=0)
    
    window_end = window_start + timedelta(minutes=10)
    
    # Go back 10 minutes for the previous window (the one we just finished)
    window_start = window_start - timedelta(minutes=10)
    window_start_ts = int(window_start.timestamp())
    window_end_ts = int(window_end.timestamp())
    
    print(f'\n{"="*80}')
    print(f'📊 AGGREGATING FEATURES FOR 10-MIN WINDOW')
    print(f'{"="*80}')
    print(f'⏰ Window Start: {window_start} (timestamp: {window_start_ts})')
    print(f'⏰ Window End:   {window_end} (timestamp: {window_end_ts})')
    print(f'{"="*80}\n')
    
    # Check if already aggregated
    existing = mongo.find_one(
        collection_name='aggregated_features_10min',
        filter={'window_start': window_start_ts}
    )
    
    if existing and existing.get('aggregation_status') == 'complete':
        print(f'✓ Window already aggregated: {window_start}')
        print(f'   Skipping...\n')
        return
    
    # STEP 1: Find BTC articles CRAWLED in this window
    print(f'🔍 STEP 1: Finding BTC articles crawled between {window_start} and {window_end}...')
    articles_crawled = list(mongo.find(
        collection_name='cmc_news',
        filter={
            'crawled_at': {'$gte': window_start_ts, '$lt': window_end_ts},
            'symbol': 'BTC'
        }
    ))
    
    if not articles_crawled:
        print(f'⚠️  No articles found crawled in this window')
        print(f'   Window: {window_start} - {window_end}\n')
        return
    
    print(f'✅ Found {len(articles_crawled)} articles crawled in this window')
    hash_ids_crawled = [a['hash_id'] for a in articles_crawled]
    print(f'   Hash IDs: {hash_ids_crawled[:5]}{"..." if len(hash_ids_crawled) > 5 else ""}\n')
    
    # STEP 2: Find corresponding NLP features
    print(f'🔍 STEP 2: Finding NLP features for these articles...')
    nlp_features = list(mongo.find(
        collection_name='article_features',
        filter={
            'hash_id': {'$in': hash_ids_crawled},
            'processing_status': 'nlp_done'
        }
    ))
    
    if not nlp_features:
        print(f'⚠️  No NLP features found for crawled articles')
        print(f'   Articles may not have been processed by NLP consumer yet\n')
        return
    
    print(f'✅ Found NLP features for {len(nlp_features)} articles')
    nlp_hash_ids = [f['hash_id'] for f in nlp_features]
    print(f'   Hash IDs with NLP: {nlp_hash_ids[:5]}{"..." if len(nlp_hash_ids) > 5 else ""}\n')
    
    # STEP 3: Find corresponding LLM sentiments
    print(f'🔍 STEP 3: Finding LLM sentiments for these articles...')
    sentiments = list(mongo.find(
        collection_name='cmc_sentiment_data',
        filter={'hash_id': {'$in': nlp_hash_ids}}
    ))
    
    if not sentiments:
        print(f'⚠️  No LLM sentiments found for articles with NLP features')
        print(f'   Articles may not have been processed by LLM consumer yet\n')
        return
    
    print(f'✅ Found LLM sentiments for {len(sentiments)} articles')
    sentiment_hash_ids = [s['hash_id'] for s in sentiments]
    print(f'   Hash IDs with LLM: {sentiment_hash_ids[:5]}{"..." if len(sentiment_hash_ids) > 5 else ""}\n')
    
    # STEP 4: Match articles with both NLP and LLM features
    print(f'🔗 STEP 4: Matching articles with BOTH NLP and LLM features...')
    sentiment_map = {s['hash_id']: s for s in sentiments}
    nlp_map = {f['hash_id']: f for f in nlp_features}
    
    complete_articles = []
    for hash_id in nlp_hash_ids:
        if hash_id in sentiment_map and hash_id in nlp_map:
            complete_articles.append({
                'hash_id': hash_id,
                'nlp': nlp_map[hash_id],
                'llm': sentiment_map[hash_id]
            })
    
    if not complete_articles:
        print(f'⚠️  No articles with BOTH NLP and LLM features')
        print(f'   NLP count: {len(nlp_features)}, LLM count: {len(sentiments)}, Overlap: 0\n')
        return
    
    print(f'✅ Found {len(complete_articles)} articles with complete processing')
    
    # STEP 5: Aggregate LLM sentiment
    print(f'📊 STEP 5: Aggregating LLM sentiments...')
    sentiment_scores = [a['llm']['sentiment_score'] for a in complete_articles]
    confidences = [a['llm']['confidence'] for a in complete_articles]
    
    llm_sentiment_avg = weighted_average(sentiment_scores, confidences)
    llm_confidence_avg = np.mean(confidences)
    
    # STEP 6: Aggregate NLP features
    print(f'📊 STEP 6: Aggregating NLP features...')
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
    
    print(f'   ✅ Aggregated {len(nlp_features_agg)} NLP features\n')
    
    # STEP 7: Create aggregated record
    print(f'💾 STEP 7: Saving aggregated features...')
    # Fetch current BTC price
    current_price = 0.0
    try:
        import requests
        # Use CoinPaprika API (no key required, high rate limit)
        response = requests.get("https://api.coinpaprika.com/v1/tickers/btc-bitcoin")
        if response.status_code == 200:
            current_price = float(response.json().get('quotes', {}).get('USD', {}).get('price', 0.0))
            print(f"💰 Fetched current BTC Price: ${current_price}")
        else:
            print(f"⚠️ Failed to fetch BTC price: {response.text}")
    except Exception as e:
        print(f"⚠️ Error fetching BTC price: {e}")

    aggregated = {
        'window_start': window_start_ts,
        'window_end': window_end_ts,
        'window_datetime': window_start.isoformat(),
        'num_articles': len(complete_articles),
        'llm_sentiment_avg': round(llm_sentiment_avg, 4),
        'llm_confidence_avg': round(llm_confidence_avg, 4),
        'nlp_features_agg': {k: round(v, 4) if isinstance(v, float) else v 
                            for k, v in nlp_features_agg.items()},
        'btc_price': current_price,
        'aggregation_status': 'complete',
        'aggregated_at': int(datetime.utcnow().timestamp()),
        'labeled': False
    }
    
    # Upsert to aggregated_features_10min
    mongo.update_one(
        collection_name='aggregated_features_10min',
        filter={'window_start': window_start_ts},
        data={'$set': aggregated},
        upsert=True
    )
    
    print(f'✅ AGGREGATION COMPLETE!')


default_args = {
    "owner": "khangpt",
    "start_date": datetime(2024, 1, 18),
    "depends_on_past": False,
}

dag = DAG(
    DAG_NAME,
    default_args=default_args,
    description="Aggregate NLP and LLM features every 10 minutes",
    schedule_interval="*/10 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["aggregation", "nlp", "features"],
)

aggregate_task = PythonOperator(
    task_id=TASK_AGGREGATE,
    python_callable=aggregate_10min_features,
    dag=dag,
)

aggregate_task
