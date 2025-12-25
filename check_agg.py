
from database.mongodb import MongoManager
import time

def check_aggregation_result():
    mongo = MongoManager('blog-data')
    
    print("Checking aggregated_features_10min collection...")
    aggs = list(mongo.find(
        collection_name='aggregated_features_10min',
        filter={},
        sort=['window_start', -1],
        limit=5
    ))
    
    if not aggs:
        print("❌ No aggregated features found yet.")
        return

    print(f"✅ Found {len(aggs)} aggregated records!")
    for doc in aggs:
        print(f"  Window: {doc.get('window_datetime')} | Articles: {doc.get('num_articles')} | NLP: {len(doc.get('nlp_features_agg', {}))} feats")
        print(f"  LLM Sentiment: {doc.get('llm_sentiment_avg')} (Conf: {doc.get('llm_confidence_avg')})")
        print("-" * 30)

if __name__ == "__main__":
    check_aggregation_result()
