
from database.mongodb import MongoManager

def fix_sentiment_scale():
    mongo = MongoManager('blog-data')
    print("Checking for skewed sentiment scores (> 1.0)...")
    
    aggs = list(mongo.find(
        collection_name='aggregated_features_10min',
        filter={'llm_sentiment_avg': {'$gt': 1.0}}
    ))
    
    if not aggs:
        print("✅ No skewed records found.")
        return

    print(f"⚠️ Found {len(aggs)} records with score > 1.0. Fixing...")
    
    for doc in aggs:
        old_score = doc.get('llm_sentiment_avg', 0.0)
        # Assuming it was 0-100 scale, map to -1 to 1?
        # Wait, the bug was: score * 100. So score 1.0 became 100.
        # But if the original model output was truly range -1 to 1, then multiplying only made it huge.
        # If I simply divide by 100?
        # 100 -> 1.0
        # -100 -> -1.0
        # 0 -> 0.0
        # 65 -> 0.65.
        # This seems safe.
        new_score = old_score / 100.0
        
        # Clamp just in case
        new_score = max(-1.0, min(1.0, new_score))
        
        mongo.update_one(
            'aggregated_features_10min', 
            {'_id': doc['_id']}, 
            {'$set': {'llm_sentiment_avg': new_score}}
        )
        print(f"  Fixed window {doc.get('window_datetime')}: {old_score} -> {new_score}")

    print("✅ Fix complete.")

if __name__ == "__main__":
    fix_sentiment_scale()
