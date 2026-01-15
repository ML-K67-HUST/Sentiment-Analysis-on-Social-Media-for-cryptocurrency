import json
import time
import sys
import os

# Allow running from consumer directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tqdm import tqdm
from kafka import KafkaConsumer, KafkaProducer
from database.mongodb import MongoManager
from bson.objectid import ObjectId
from LLM.sentiment_agent import infer_policy, infer_sentiment
from data_constructor import construct_unlabeled_dataset
from backend.config import config

kafka_server = [config.KAFKA_BOOTSTRAP_SERVERS]
topic = config.KAFKA_TOPIC

mongo_client = MongoManager(config.MONGODB_DATABASE)

consumer = KafkaConsumer(
    bootstrap_servers=kafka_server,
    group_id="llm-sentiment-group",
    value_deserializer=json.loads,
    auto_offset_reset="earliest",
)

consumer.subscribe([topic])  # CRITICAL: subscribe() requires a LIST

print("=" * 80, flush=True)
print("🚀 LLM SENTIMENT CONSUMER", flush=True)
print("=" * 80, flush=True)
print(f"Topic: {topic}", flush=True)
print(f"Group: llm-sentiment-group", flush=True)
print(f"Model: Gemini 2.0 Flash Lite (Free Tier)", flush=True)
print(f"Rate Limit: 15 req/min → 60s sleep between articles", flush=True)
print("=" * 80, flush=True)
print("⏳ Waiting for messages...\n", flush=True)

while True:
    for message in consumer:
        data = message
        articles = data.value["hash_ids"]
        
        print(f"\n📦 Batch: {len(articles)} articles | Offset: {message.offset}", flush=True)
        
        # Process with progress bar
        success_count = 0
        error_count = 0
        skip_count = 0
        
        pbar = tqdm(articles, desc="Processing", unit="article", ncols=100)
        
        for article in pbar:
            pbar.set_description(f"📄 {article[:16]}...")
            
            try:
                # Get article from DB
                record = mongo_client.find_one(
                    collection_name='cmc_news',
                    filter={"hash_id": article}
                )
                
                if not record:
                    skip_count += 1
                    pbar.set_postfix({"✅": success_count, "⏭️": skip_count, "❌": error_count}, refresh=True)
                    continue
                
                # Extract data
                title = record['title']
                symbol = record['symbol']
                content = record['content']
                
                # Call LLM for sentiment
                infered_policy = infer_policy(content)
                
                if not infered_policy:
                    error_count += 1
                    pbar.set_postfix({"✅": success_count, "⏭️": skip_count, "❌": error_count}, refresh=True)
                    continue
                
                # Parse sentiment
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
                
                # Store sentiment data
                data_to_store = {
                    "btc_sentiment": btc_sentiment,
                    "timestamp": record['timestamp'],
                    "hash_id": article,
                    "source": "cmc_news",
                    "symbol": symbol,
                    "source_data": [{
                        "title": title,
                        "url": record['url'],
                        "symbol": symbol,
                        "content": content,
                        "timestamp": record['timestamp'],
                        "hash_id": article,
                        "category": record.get('category', '')
                    }]
                }
                
                mongo_client.insert_one(collection_name='cmc_sentiment_data', data=data_to_store)
                
                # Store unlabeled data
                sentiment_score = infer_sentiment(infered_policy)
                unlabeled_data = construct_unlabeled_dataset(sentiment_score)
                mongo_client.insert_one(collection_name='cmc_unlabeled_data', data=unlabeled_data)
                
                success_count += 1
                pbar.set_postfix({"✅": success_count, "⏭️": skip_count, "❌": error_count}, refresh=True)
                
                # Sleep to avoid rate limit
                time.sleep(60)
                
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    pbar.write(f"⚠️  Rate limit hit! Waiting 60s...")
                else:
                    pbar.write(f"❌ Error: {error_msg[:100]}...")
                pbar.set_postfix({"✅": success_count, "⏭️": skip_count, "❌": error_count}, refresh=True)
                time.sleep(60)
        
        # Summary after batch
        print(f"\n✅ Batch complete: {success_count} success, {skip_count} skipped, {error_count} errors\n", flush=True)
    # print(type(data))
    
    
