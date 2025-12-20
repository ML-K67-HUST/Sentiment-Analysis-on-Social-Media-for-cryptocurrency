"""
Script to label existing CoinMarketCap news data with sentiment using LLM.
Run this once to add sentiment labels to existing data.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mongodb import MongoManager
from LLM.sentiment_agent import infer_policy
from config import config
import time
from datetime import datetime


def label_news_sentiment(limit=100):
    """
    Label existing news articles with sentiment using LLM.
    
    Args:
        limit: Maximum number of articles to process
    """
    print(f"🤖 Starting sentiment labeling with {config.LLM_PROVIDER}...")
    print(f"📊 Processing up to {limit} articles")
    
    # Connect to MongoDB
    mongo_client = MongoManager('blog-data')
    
    # Find articles without sentiment
    articles = mongo_client.find(
        collection_name='cmc_news',
        filter={
            '$or': [
                {'sentiment': {'$exists': False}},
                {'sentiment': None}
            ]
        },
        sort=("timestamp", -1),
        limit=limit
    )
    
    print(f"📰 Found {len(articles)} articles to label")
    
    if not articles:
        print("✅ All articles already labeled!")
        return
    
    # Process each article
    success_count = 0
    error_count = 0
    
    for i, article in enumerate(articles, 1):
        try:
            article_id = article['_id']
            title = article.get('title', '')
            content = article.get('content', '')
            
            # Combine title and content for analysis
            text = f"{title}\n\n{content[:500]}"  # Limit to 500 chars
            
            print(f"\n[{i}/{len(articles)}] Processing: {title[:60]}...")
            
            # Get sentiment from LLM (infer_policy only takes text parameter)
            result = infer_policy(text=text)
            
            sentiment = result.get('sentiment', 'neutral')
            confidence = result.get('confidence', 0.0)
            reasoning = result.get('reasoning', '')
            
            # Update article with sentiment
            mongo_client.update_one(
                collection_name='cmc_news',
                filter={'_id': article_id},
                data={
                    '$set': {
                        'sentiment': sentiment,
                        'sentiment_confidence': confidence,
                        'sentiment_reasoning': reasoning,
                        'sentiment_labeled_at': int(datetime.now().timestamp())
                    }
                },
                upsert=False
            )
            
            success_count += 1
            print(f"   ✅ Sentiment: {sentiment} (confidence: {confidence:.2f})")
            
            # Rate limiting to avoid API throttling
            if i % 5 == 0:
                print("   ⏸️  Pausing 2s to avoid rate limits...")
                time.sleep(2)
            else:
                time.sleep(0.5)
                
        except Exception as e:
            error_count += 1
            print(f"   ❌ Error: {str(e)}")
            continue
    
    print(f"\n" + "="*60)
    print(f"📊 Labeling Complete!")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📈 Success Rate: {(success_count/(success_count+error_count)*100):.1f}%")
    print("="*60)


def check_sentiment_stats():
    """Check sentiment distribution in database"""
    mongo_client = MongoManager('blog-data')
    
    # Count articles with/without sentiment
    total = mongo_client.find(
        collection_name='cmc_news',
        filter={}
    )
    
    with_sentiment = mongo_client.find(
        collection_name='cmc_news',
        filter={'sentiment': {'$exists': True, '$ne': None}}
    )
    
    print(f"\n📊 Sentiment Statistics:")
    print(f"   Total articles: {len(total)}")
    print(f"   Labeled: {len(with_sentiment)}")
    print(f"   Unlabeled: {len(total) - len(with_sentiment)}")
    
    # Count by sentiment
    positive = len([a for a in with_sentiment if a.get('sentiment') == 'positive'])
    negative = len([a for a in with_sentiment if a.get('sentiment') == 'negative'])
    neutral = len([a for a in with_sentiment if a.get('sentiment') == 'neutral'])
    
    if with_sentiment:
        print(f"\n   Positive: {positive} ({positive/len(with_sentiment)*100:.1f}%)")
        print(f"   Negative: {negative} ({negative/len(with_sentiment)*100:.1f}%)")
        print(f"   Neutral: {neutral} ({neutral/len(with_sentiment)*100:.1f}%)")


if __name__ == "__main__":
    print("="*60)
    print("🚀 Sentiment Labeling Script")
    print("="*60)
    
    # Validate API key
    try:
        config.validate()
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n💡 Please set your API key in .env file:")
        print(f"   {config.LLM_PROVIDER.upper()}_API_KEY=your_key_here")
        sys.exit(1)
    
    # Check current stats
    check_sentiment_stats()
    
    # Ask for confirmation
    print("\n" + "="*60)
    response = input("🤔 Do you want to start labeling? (y/n): ").strip().lower()
    
    if response == 'y':
        # Get number of articles to process
        try:
            limit_input = input("📊 How many articles to process? (default: 100): ").strip()
            limit = int(limit_input) if limit_input else 100
        except ValueError:
            limit = 100
        
        # Start labeling
        label_news_sentiment(limit=limit)
        
        # Show final stats
        check_sentiment_stats()
    else:
        print("❌ Labeling cancelled")

