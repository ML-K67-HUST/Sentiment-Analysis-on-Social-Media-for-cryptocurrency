import os
import sys
import time
import json
from tqdm import tqdm
from bson.objectid import ObjectId

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import config
    from database.mongodb import MongoManager
    from LLM.sentiment_agent import infer_policy, infer_sentiment
    from data_constructor import construct_unlabeled_dataset
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def manual_process_sentiment(limit=100):
    print("=" * 80)
    print("🚀 MANUAL SENTIMENT PROCESSING SCRIPT")
    print("=" * 80)

    # Initialize MongoDB
    try:
        # Auto-fix connection string for local execution
        conn_str = config.MONGODB_CONNECTION_STRING
        if "@mongodb" in conn_str:
            print("⚠️  Detected Docker hostname 'mongodb'. Switching to 'localhost' for local execution.")
            conn_str = conn_str.replace("@mongodb", "@localhost")
            
        mongo_client = MongoManager('blog-data', uri=conn_str)
        print(f"✅ MongoDB connected successfully to {conn_str}")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return

    # Find articles that haven't been processed yet
    # We can check by hash_id in cmc_sentiment_data
    print("🔍 Fetching processed hash_ids...")
    processed_hashes = mongo_client.distinct('cmc_sentiment_data', 'hash_id')
    print(f"ℹ️  Found {len(processed_hashes)} already processed articles.")

    # Fetch candidates from cmc_news
    # We need to find articles NOT in processed_hashes
    print(f"🔍 Fetching {limit} unprocessed articles from cmc_news...")
    
    # Using aggregation/find to filter might be slow if lists are huge, but fine for 100 items for now.
    # An easier way is to fetch a batch and filter in python if the total dataset isn't massive, 
    # or use $nin, but $nin with large arrays is slow. 
    # Let's try to fetch a bit more and filter carefully.
    
    # Better approach for scalability: Iterate and check existance, or use a set for O(1) lookup
    processed_set = set(processed_hashes)
    
    pipeline = [
        {"$match": {"hash_id": {"$nin": list(processed_set)}}},
        {"$limit": limit}
    ]
    
    # If the list is too big for $nin, we might need a different strategy, 
    # but let's assume it fits for this manual run.
    if len(processed_set) > 10000:
        print("⚠️  Large number of processed items. Optimization might be needed. Fetching candidates iteratively...")
        # Fallback: Fetch latest and filter python side
        candidates = []
        offset = 0
        batch_size = 100
        while len(candidates) < limit:
            batch = mongo_client.find('cmc_news', sort=[('_id', -1)], offset=offset, limit=batch_size)
            if not batch:
                break
            
            for doc in batch:
                if doc.get('hash_id') not in processed_set:
                    candidates.append(doc)
                    if len(candidates) >= limit:
                        break
            offset += batch_size
    else:
         # Sort by timestamp DESC to get largest/latest news first
         candidates = mongo_client.find(
             'cmc_news', 
             filter={"hash_id": {"$nin": list(processed_set)}}, 
             sort=("timestamp", -1),
             limit=limit
         )

    print(f"✅ Found {len(candidates)} articles to process.")
    
    if not candidates:
        print("No new articles to process.")
        return

    success_count = 0
    error_count = 0
    skip_count = 0

    pbar = tqdm(candidates, desc="Processing", unit="article", ncols=100)

    for record in pbar:
        title = record.get('title', 'No Title')
        article_hash = record.get('hash_id')
        pbar.set_description(f"📄 {title[:20]}...")

        if not article_hash:
            skip_count += 1
            continue

        try:
            content = record.get('content', '')
            if not content:
                 skip_count += 1
                 continue

            symbol = record.get('symbol', 'BTC')
            
            # Call LLM
            infered_policy = {}
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    infered_policy = infer_policy(content)
                    break
                except Exception as e:
                    error_msg = str(e)
                    if "ALL_KEYS_EXHAUSTED" in error_msg:
                        pbar.write("⚠️  Rate limit (ALL KEYS): Waiting 30s...")
                        time.sleep(30)
                        retry_count += 1
                    elif "429" in error_msg:
                        pbar.write("⚠️  429 Occurred, waiting 10s...")
                        time.sleep(10)
                        retry_count += 1
                    else:
                        pbar.write(f"❌ Inference Error: {e}")
                        break
            
            if not infered_policy:
                error_count += 1
                continue

            # Parse results (Reuse logic from llm_consumer.py)
            btc_sentiment = {}
            if "metrics" in infered_policy:
                for policy in infered_policy["metrics"]:
                    btc_sentiment[policy['policy']] = {
                        "reasoning": policy['reasoning'],
                        "result": policy["classification"]
                    }
            else:
                 btc_sentiment["bitcoin_sentiment"] = {
                    "reasoning": infered_policy.get('reasoning', ''),
                    "result": infered_policy.get('sentiment', 'unknown'),
                    "confidence": infered_policy.get('confidence', 0.0)
                }

            sentiment_score = infer_sentiment(infered_policy)
            
            # Prepare data objects
            data_to_store = {
                "btc_sentiment": btc_sentiment,
                "sentiment_score": sentiment_score,
                "confidence": infered_policy.get('confidence', 0.0),
                "timestamp": record.get('timestamp'),
                "hash_id": article_hash,
                "source": "cmc_news",
                "symbol": symbol,
                "source_data": [{
                    "title": title,
                    "url": record.get('url'),
                    "symbol": symbol,
                    "content": content,
                    "timestamp": record.get('timestamp'),
                    "hash_id": article_hash,
                    "category": record.get('category', '')
                }]
            }

            unlabeled_data = construct_unlabeled_dataset(sentiment_score)
            
            # Insert into DB
            mongo_client.insert_one(collection_name='cmc_sentiment_data', data=data_to_store)
            mongo_client.insert_one(collection_name='cmc_unlabeled_data', data=unlabeled_data)
            
            success_count += 1
            # Small delay to be nice to API
            time.sleep(1) 

        except Exception as e:
            error_count += 1
            pbar.write(f"❌ Unexpected Error: {e}")

    print("\n" + "=" * 80)
    print(f"🎉 DONE! Processed {success_count} articles.")
    print(f"❌ Errors: {error_count}")
    print(f"⏭️  Skipped: {skip_count}")
    print("=" * 80)

if __name__ == "__main__":
    manual_process_sentiment(limit=10)
