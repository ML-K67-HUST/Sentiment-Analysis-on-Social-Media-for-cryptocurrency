from pymongo import MongoClient
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import config

conn_str = config.MONGODB_CONNECTION_STRING
if "@mongodb" in conn_str:
    conn_str = conn_str.replace("@mongodb", "@localhost")

print(f"📊 Connecting directly to: {conn_str}")
client = MongoClient(conn_str)
db = client['blog-data']

print("📊 Checking All Collections...")
all_cols = db.list_collection_names()
print(f"   Found collections: {all_cols}")

collections = [
    'cmc_news',
    'article_features',
    'cmc_sentiment_data',
    'aggregated_features_10min'
]

for col in collections:
    count = db[col].count_documents({})
    print(f"   {col}: {count}")

print("\n🔍 Checking Aggregated Features Status...")
agg_total = db['aggregated_features_10min'].count_documents({})
agg_labeled = db['aggregated_features_10min'].count_documents({'labeled': True})
agg_unlabeled = db['aggregated_features_10min'].count_documents({'labeled': False})

print(f"   Total Aggregated: {agg_total}")
print(f"   Labeled: {agg_labeled}")
print(f"   Unlabeled: {agg_unlabeled}")

print("\n🔍 Checking Unlabeled Data...")
unlabeled_count = db['cmc_unlabeled_data'].count_documents({})
print(f"   Unlabeled Data: {unlabeled_count}")

if agg_unlabeled > 0:
    print("\n   ⚠️ Found unlabeled aggregations! These were skipped by export.")

