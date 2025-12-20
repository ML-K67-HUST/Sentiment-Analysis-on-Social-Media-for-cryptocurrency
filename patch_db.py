
from database.mongodb import MongoManager
from datetime import datetime

def patch_timestamps():
    mongo = MongoManager('blog-data')
    print("Fetching articles with string timestamps...")
    # Find records where crawled_at is a string
    cursor = mongo.find('cmc_news', filter={'crawled_at': {'$type': 'string'}})
    
    count = 0
    for doc in cursor:
        try:
            iso_str = doc['crawled_at']
            # Parse ISO string to timestamp
            # Format from logs: 2025-12-20T14:20:06.328930
            dt = datetime.fromisoformat(iso_str)
            ts = int(dt.timestamp())
            
            mongo.update_one('cmc_news', {'_id': doc['_id']}, {'$set': {'crawled_at': ts}})
            count += 1
        except Exception as e:
            print(f"Failed to update {doc.get('_id')}: {e}")
            
    print(f"✅ Patched {count} records.")

if __name__ == "__main__":
    patch_timestamps()
