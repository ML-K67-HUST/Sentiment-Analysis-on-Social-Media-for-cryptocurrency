from database.mongodb import MongoManager
from datetime import datetime

# Force use of localhost for this debug script if running locally
conn_str = "mongodb://admin:change_me_in_production@localhost:27018"
mongo_client = MongoManager('blog-data', uri=conn_str)

print("Fetching latest 50 sentiments...")
sentiments = list(mongo_client.find(
    'cmc_sentiment_data', 
    limit=50,
    sort=('_id', -1) # Assuming _id is time-based (ObjectId) or we can look at a specific timestamp if exists
))

print(f"Found {len(sentiments)} records.")

if not sentiments:
    exit()

hash_ids = [s.get('hash_id') for s in sentiments]

# Fetch corresponding articles to get 'crawled_at' or 'timestamp'
articles = list(mongo_client.find('cmc_news', filter={'hash_id': {'$in': hash_ids}}))
article_map = {a.get('hash_id'): a for a in articles}

print("\n--- Processed Articles Timestamps ---")
timestamps = []
for s in sentiments:
    h = s.get('hash_id')
    a = article_map.get(h)
    if a:
        ts = a.get('timestamp') # Publish time
        crawled = a.get('crawled_at') # Crawl time
        
        # Aggregation uses 'crawled_at' usually, or 'timestamp'?
        # aggregate_10min_features.py uses 'crawled_at' in filter.
        
        if crawled:
             timestamps.append(crawled)
             dt = datetime.fromtimestamp(int(crawled))
             print(f"Hash: {h[:10]}... | Crawled: {dt} | TS: {crawled}")
        else:
             print(f"Hash: {h[:10]}... | MISSING crawled_at")
    else:
        print(f"Hash: {h[:10]}... | Article NOT FOUND")

if timestamps:
    min_ts = min(timestamps)
    max_ts = max(timestamps)
    print(f"\nRange: {datetime.fromtimestamp(min_ts)} to {datetime.fromtimestamp(max_ts)}")
