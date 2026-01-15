from database.mongodb import MongoManager
from datetime import datetime

conn_str = "mongodb://admin:change_me_in_production@localhost:27018"
mongo_client = MongoManager('blog-data', uri=conn_str)

# One of the hashes from today
test_hash = "694e2491a329d2f2d1e04c55" 
# Actually I need the full hash. The previous log truncated it.
# Let's fetch the latest one again.

print("Fetching latest sentiment to get full hash...")
latest_sentiment = mongo_client.find_one(
    'cmc_sentiment_data', 
    sort=('_id', -1)
)

if not latest_sentiment:
    print("No sentiment found.")
    exit()

full_hash = latest_sentiment.get('hash_id')
print(f"Checking Hash: {full_hash}")

nlp = mongo_client.find_one('article_features', filter={'hash_id': full_hash})

if nlp:
    print("✅ NLP Feature Found!")
    print(f"   Keys: {list(nlp.keys())}")
else:
    print("❌ NLP Feature MISSING!")
    # Check if we have ANY nlp features recently
    latest_nlp = mongo_client.find_one('article_features', sort=('_id', -1))
    if latest_nlp:
        print(f"   Latest NLP was for hash: {latest_nlp.get('hash_id')}")
    else:
        print("   No NLP features found at all.")
