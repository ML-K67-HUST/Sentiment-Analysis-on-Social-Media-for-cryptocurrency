"""
NLP Feature Engineering Consumer
Subscribes to Kafka coinmarketcap-news topic and extracts NLP features
"""

import json
import sys
import os

# Allow running from consumer directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka import KafkaConsumer
from database.mongodb import MongoManager
from nlp.feature_extractor import NLPFeatureExtractor
import time
from datetime import datetime
from backend.config import config

kafka_server = [config.KAFKA_BOOTSTRAP_SERVERS]
topic = config.KAFKA_TOPIC

mongo_client = MongoManager(config.MONGODB_DATABASE)
nlp_extractor = NLPFeatureExtractor()

consumer = KafkaConsumer(
    bootstrap_servers=kafka_server,
    group_id="nlp-feature-group",
    value_deserializer=json.loads,
    auto_offset_reset="earliest",
)

consumer.subscribe([topic])  # CRITICAL: subscribe() requires a LIST

print(f"🚀 [NLP Consumer] Started")
print(f"📍 Topic: {topic}, Group: nlp-feature-group")
print(f"⏳ Waiting for messages...\n")

from tqdm import tqdm
import sys

# ... imports ...

while True:
    for message in consumer:
        print(f"\n🔬 [NLP Consumer] Received message")
        print(f"   Partition: {message.partition}, Offset: {message.offset}")
        
        articles = message.value.get("hash_ids", [])
        print(f"   Processing {len(articles)} articles for NLP features...\n")
        
        # Use tqdm for progress bar, force output to stdout for docker logs
        for hash_id in tqdm(articles, file=sys.stdout, desc="Processing batch"):
            try:
                # Get article from cmc_news
                record = mongo_client.find_one(
                    collection_name='cmc_news',
                    filter={"hash_id": hash_id}
                )
                
                if not record:
                    # print(f"⚠️  Article not found: {hash_id}") # Reduce noise
                    continue
                    
                # FILTER: Only process BTC articles
                symbol = record.get('symbol')
                if symbol != 'BTC':
                    # print(f"⏭️ Skipping non-BTC article: {symbol}") # Reduce noise
                    continue
                
                # Check if already processed
                existing = mongo_client.find_one(
                    collection_name='article_features',
                    filter={'hash_id': hash_id}
                )
                
                if existing and existing.get('processing_status') == 'nlp_done':
                    print(f"✓ Already processed: {hash_id}")
                    continue
                
                # Extract NLP features
                content = record.get('content', '')
                
                if not content:
                    print(f"⚠️  No content for article: {hash_id}")
                    continue
                
                print(f"📊 Extracting NLP features...")
                nlp_features = nlp_extractor.extract_features(content)
                
                # Prepare document
                feature_doc = {
                    'hash_id': hash_id,
                    'timestamp': record.get('timestamp', time.time()),
                    'crawled_at': record.get('crawled_at', int(time.time())),
                    'nlp_features': nlp_features,
                    'processing_status': 'nlp_done',
                    'processed_at': int(datetime.now().timestamp())
                }
                
                # Upsert to article_features
                mongo_client.update_one(
                    collection_name='article_features',
                    filter={'hash_id': hash_id},
                    data={'$set': feature_doc},
                    upsert=True
                )
                
                print(f"✅ NLP features extracted and saved")
                print(f"   Features: compound={nlp_features['compound_score']:.2f}, "
                      f"words={nlp_features['word_count']}, "
                      f"btc_mentions={nlp_features['btc_mention_count']}")
                
            except Exception as e:
                print(f"❌ Error processing {hash_id}: {e}")
                import traceback
                traceback.print_exc()
