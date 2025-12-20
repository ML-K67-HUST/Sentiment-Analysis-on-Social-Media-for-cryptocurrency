
from database.mongodb import MongoManager
from datetime import datetime, timedelta

def force_insert_agg():
    mongo = MongoManager('blog-data')
    
    # Create a dummy aggregation for NOW
    now = datetime.utcnow()
    window_start = int((now - timedelta(minutes=10)).timestamp())
    
    dummy_data = {
        'window_start': window_start,
        'window_end': int(now.timestamp()),
        'window_datetime': (now - timedelta(minutes=10)).isoformat(),
        'num_articles': 15,
        'llm_sentiment_avg': 0.65, # Positive sentiment
        'llm_confidence_avg': 0.88,
        'unique_articles': 12,
        'nlp_features_agg': {
            'avg_compound_score': 0.45,
            'total_btc_mention_count': 25
        },
        'aggregation_status': 'complete',
        'aggregated_at': int(now.timestamp()),
        'labeled': False
    }
    
    mongo.update_one(
        collection_name='aggregated_features_10min',
        filter={'window_start': window_start},
        data={'$set': dummy_data},
        upsert=True
    )
    
    print(f"✅ Forced inserted dummy aggregation for window {window_start}")

if __name__ == "__main__":
    force_insert_agg()
