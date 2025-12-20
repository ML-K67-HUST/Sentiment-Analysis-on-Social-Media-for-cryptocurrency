
from database.mongodb import MongoManager
from datetime import datetime, timedelta

def touch_timestamps():
    mongo = MongoManager('blog-data')
    
    print("Touching recent articles to make them 'fresh'...")
    # Get recent 10 articles
    cursor = mongo.find(
        collection_name='cmc_news',
        filter={'symbol': 'BTC'},
        sort=['crawled_at', -1],
        limit=10
    )
    
    # Set time to 5 mins ago
    fresh_time = int((datetime.utcnow() - timedelta(minutes=15)).timestamp())
    
    count = 0
    ids = []
    for doc in cursor:
        mongo.update_one('cmc_news', {'_id': doc['_id']}, {'$set': {'crawled_at': fresh_time}})
        ids.append(doc.get('hash_id'))
        count += 1
            
    print(f"✅ Touched {count} records to time {fresh_time} (Iso: {datetime.utcnow() - timedelta(minutes=5)}).")
    print(f"Hash IDs: {ids}")

if __name__ == "__main__":
    touch_timestamps()
