"""
Manual NLP Processing Script
Backfills NLP features for articles that have sentiment data but are missing NLP features.
"""
import time
from datetime import datetime
from tqdm import tqdm
import sys
import os
# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.mongodb import MongoManager
from nlp.feature_extractor import NLPFeatureExtractor
from config import config

def manual_process_nlp():
    print("🚀 Starting Manual NLP Processing...")
    
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

    nlp_extractor = NLPFeatureExtractor()
    
    # 1. content exists
    # 2. symbol is BTC
    # 3. We have computed sentiment for it (optional, but good for saving time)
    # 4. BUT no nlp features yet
    
    # Let's find articles that we recently processed sentiments for
    print("\n🔍 Step 1: Finding articles needing NLP...")
    
    # Get hash_ids from cmc_sentiment_data (latest 200 to be safe)
    sentiments = list(mongo_client.find('cmc_sentiment_data', limit=200, sort=('_id', -1)))
    sentiment_hashes = [s.get('hash_id') for s in sentiments]
    
    print(f"   Found {len(sentiment_hashes)} recent sentiment records.")
    
    # Find which ones are missing in article_features
    processed_nlp = list(mongo_client.find(
        'article_features', 
        filter={'hash_id': {'$in': sentiment_hashes}}
    ))
    processed_hashes = {p.get('hash_id') for p in processed_nlp}
    
    missing_hashes = [h for h in sentiment_hashes if h not in processed_hashes]
    
    print(f"   Found {len(missing_hashes)} articles missing NLP features.")
    
    if not missing_hashes:
        print("✅ All recent articles have NLP features. Nothing to do.")
        return

    # Process them
    print(f"\n⚙️  Processing {len(missing_hashes)} articles...")
    
    success_count = 0
    
    for hash_id in tqdm(missing_hashes):
        try:
            # Get article content
            article = mongo_client.find_one('cmc_news', filter={'hash_id': hash_id})
            
            if not article:
                print(f"⚠️  Article not found for hash: {hash_id}")
                continue
                
            content = article.get('content', '')
            if not content:
                print(f"⚠️  No content for article: {hash_id}")
                continue
                
            # Extract features
            nlp_features = nlp_extractor.extract_features(content)
            
            # Prepare document
            feature_doc = {
                'hash_id': hash_id,
                'timestamp': article.get('timestamp', time.time()),
                'crawled_at': article.get('crawled_at', int(time.time())),
                'nlp_features': nlp_features,
                'processing_status': 'nlp_done',
                'processed_at': int(datetime.now().timestamp())
            }
            
            # Save
            mongo_client.update_one(
                collection_name='article_features',
                filter={'hash_id': hash_id},
                data={'$set': feature_doc},
                upsert=True
            )
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error processing {hash_id}: {e}")
            
    print(f"\n✅ Completed! Successfully processed {success_count}/{len(missing_hashes)} articles.")

if __name__ == "__main__":
    manual_process_nlp()
