
from database.mongodb import MongoManager

def fix_negative_scale():
    mongo = MongoManager('blog-data')
    print("Checking for skewed negative sentiment scores (< -1.0)...")
    
    aggs = list(mongo.find(
        collection_name='aggregated_features_10min',
        filter={'llm_sentiment_avg': {'$lt': -1.0}}
    ))
    
    if not aggs:
        print("✅ No skewed negative records found.")
        return

    print(f"⚠️ Found {len(aggs)} records with score < -1.0. Fixing...")
    
    for doc in aggs:
        old_score = doc.get('llm_sentiment_avg', 0.0)
        # Fix: divide by 100
        new_score = old_score / 100.0
        
        # Clamp just in case
        new_score = max(-1.0, min(1.0, new_score))
        
        mongo.update_one(
            'aggregated_features_10min', 
            {'_id': doc['_id']}, 
            {'$set': {'llm_sentiment_avg': new_score}}
        )
        print(f"  Fixed window {doc.get('window_datetime')}: {old_score} -> {new_score}")

    print("✅ Negative Fix complete.")

if __name__ == "__main__":
    fix_negative_scale()
