
from database.mongodb import MongoManager
from datetime import datetime
import time

def debug_aggregation():
    mongo = MongoManager('blog-data')
    
    print(f"Current UTC Time: {datetime.utcnow()}")
    print("-" * 50)
    
    # 1. Check latest BTC articles in cmc_news
    print("Checking latest BTC articles in 'cmc_news'...")
    articles = list(mongo.find(
        collection_name='cmc_news',
        filter={'symbol': 'BTC'},
        sort=['crawled_at', -1],
        limit=5
    ))
    
    if not articles:
        print("❌ No BTC articles found in cmc_news!")
        return

    print(f"Found {len(articles)} recent BTC articles:")
    for doc in articles:
        crawled_at = doc.get('crawled_at')
        if isinstance(crawled_at, (int, float)):
            crawled_dt = datetime.fromtimestamp(crawled_at)
        else:
            crawled_dt = crawled_at
        print(f"  Hash: {doc.get('hash_id')[:10]}... | Crawled: {crawled_dt} ({crawled_at})")
        
        hash_id = doc.get('hash_id')
        
        # 2. Check NLP Features
        nlp = mongo.find_one('article_features', {'hash_id': hash_id})
        nlp_status = "✅ Found" if nlp else "❌ Missing"
        if nlp:
            nlp_status += f" (Status: {nlp.get('processing_status')})"
            
        # 3. Check LLM Sentiment
        llm = mongo.find_one('cmc_sentiment_data', {'hash_id': hash_id})
        llm_status = "✅ Found" if llm else "❌ Missing"
        
        print(f"     NLP: {nlp_status}")
        print(f"     LLM: {llm_status}")
        print("-" * 30)

if __name__ == "__main__":
    debug_aggregation()
