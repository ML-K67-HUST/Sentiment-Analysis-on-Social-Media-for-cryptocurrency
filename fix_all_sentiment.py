from database.mongodb import MongoManager

def fix_all_sentiment():
    mongo = MongoManager('blog-data')
    print("Fixing ALL sentiment scores to ensure they are in -1.0 to 1.0 range...")
    
    # Get all aggregations
    aggs = list(mongo.find(
        collection_name='aggregated_features_10min',
        filter={}
    ))
    
    if not aggs:
        print("✅ No records found.")
        return

    print(f"Found {len(aggs)} records total. Checking...")
    
    fixed_count = 0
    for doc in aggs:
        old_score = doc.get('llm_sentiment_avg', 0.0)
        
        # If score is outside -1.0 to 1.0, it's likely scaled wrong
        if abs(old_score) > 1.0:
            # Assume it was multiplied by 100
            new_score = old_score / 100.0
            
            # Clamp to safe range
            new_score = max(-1.0, min(1.0, new_score))
            
            mongo.update_one(
                'aggregated_features_10min', 
                {'_id': doc['_id']}, 
                {'$set': {'llm_sentiment_avg': new_score}}
            )
            print(f"  Fixed {doc.get('window_datetime')}: {old_score} -> {new_score}")
            fixed_count += 1
        else:
            # Score looks good, just verify it's reasonable
            if old_score != 0:
                print(f"  OK: {doc.get('window_datetime')}: {old_score}")
    
    print(f"\n✅ Fixed {fixed_count} records. System is now clean.")

if __name__ == "__main__":
    fix_all_sentiment()
