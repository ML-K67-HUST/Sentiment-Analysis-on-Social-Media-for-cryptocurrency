"""
LLM Sentiment Labeling DAG
===========================
Automatically label newly crawled articles with LLM sentiment analysis.

Schedule: Every hour at :10 (10 minutes after CMC crawler)
Logic: Label articles that were crawled in the last 70 minutes (to catch any stragglers)
"""

from database.mongodb import MongoManager
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import sys
import os

# Add backend path to import LLM sentiment agent
sys.path.insert(0, '/opt/airflow/dags')

DAG_NAME = "llm_sentiment_labeling_1h"
TASK_LABEL_SENTIMENT = "label_new_articles_with_llm"


def label_new_articles():
    """
    Label newly crawled articles with LLM sentiment analysis.
    
    Process:
    1. Find articles from cmc_news that were crawled in the last 70 minutes
    2. Check if they already have sentiment in cmc_sentiment_data
    3. Call Gemini LLM to analyze sentiment
    4. Store results in cmc_sentiment_data collection
    """
    # Import here to avoid issues if not available during DAG parsing
    try:
        from LLM.sentiment_agent import infer_policy
    except ImportError:
        print("❌ Cannot import sentiment_agent. Make sure backend is accessible.")
        print("   This DAG needs access to backend/LLM/sentiment_agent.py")
        return
    
    mongo_client = MongoManager('blog-data')
    
    # Look for articles crawled in the last 70 minutes
    # (CMC crawler runs every hour, we run 10 min after, so catch everything)
    time_threshold = datetime.utcnow() - timedelta(minutes=70)
    
    print(f'🔍 Looking for articles crawled after {time_threshold.strftime("%Y-%m-%d %H:%M:%S")} UTC')
    print(f'   Current time: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC')
    
    # Find articles from cmc_news that are recent (based on crawl time, not publish time!)
    filter_condition = {
        "crawled_at": {"$gte": time_threshold.isoformat()},
        "title": {"$exists": True, "$ne": None},
        "content": {"$exists": True, "$ne": None}
    }
    
    articles = list(mongo_client.find(
        collection_name="cmc_news",
        filter=filter_condition,
    ))
    
    if not articles:
        print('✅ NO NEW ARTICLES TO LABEL')
        print(f'   Time window: Last 70 minutes from {time_threshold}')
        return
    
    print(f'📚 Found {len(articles)} articles in time window')
    
    # Check which ones already have sentiment
    unlabeled_articles = []
    for article in articles:
        article_id = str(article.get('_id'))
        
        # Check if sentiment already exists
        existing_sentiment = mongo_client.find_one(
            collection_name="cmc_sentiment_data",
            filter={"article_id": article_id}
        )
        
        if not existing_sentiment:
            unlabeled_articles.append(article)
    
    if not unlabeled_articles:
        print('✅ ALL ARTICLES ALREADY LABELED')
        print(f'   Total checked: {len(articles)}')
        return
    
    print(f'🏷️  Need to label {len(unlabeled_articles)} articles')
    print(f'   (Already labeled: {len(articles) - len(unlabeled_articles)})')
    
    count = 0
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for article in unlabeled_articles:
        count += 1
        article_id = str(article.get('_id'))
        title = article.get('title', 'No title')[:60]
        content = article.get('content', '')
        
        print(f'\n[{count}/{len(unlabeled_articles)}] Processing: {title}...')
        
        # Skip if content is too short
        if not content or len(content) < 50:
            print(f'   ⏭️  Skipped: Content too short ({len(content)} chars)')
            skip_count += 1
            continue
        
        try:
            # Call Gemini LLM for sentiment analysis
            result = infer_policy(content)
            
            sentiment = result.get('sentiment')
            confidence = result.get('confidence')
            reasoning = result.get('reasoning', '')
            
            # Skip if LLM failed
            if not sentiment or confidence is None or confidence == 0.0:
                print(f'   ⚠️  LLM returned invalid result, skipping...')
                error_count += 1
                continue
            
            print(f'   ✅ Sentiment: {sentiment} (confidence: {confidence})')
            
            # Store in cmc_sentiment_data
            sentiment_record = {
                'article_id': article_id,
                'title': article.get('title'),
                'url': article.get('url'),
                'content': content,
                'source': article.get('source', 'coinmarketcap'),
                'symbol': article.get('symbol', 'BTC'),
                'timestamp': article.get('timestamp'),
                'crawled_at': article.get('crawled_at'),  # Keep original crawl time
                'hash_id': article.get('hash_id'),
                
                # Sentiment fields
                'sentiment': sentiment,
                'sentiment_confidence': confidence,
                'llm_prediction': reasoning,
                'labeled_at': datetime.utcnow().isoformat(),
                'labeling_method': 'gemini-llm',
                'dag_run': 'llm_sentiment_labeling_1h'
            }
            
            mongo_client.insert_one(
                collection_name='cmc_sentiment_data',
                data=sentiment_record
            )
            
            success_count += 1
            
        except Exception as e:
            print(f'   ❌ Error: {str(e)[:100]}')
            error_count += 1
    
    print(f'\n🎉 LABELING COMPLETE')
    print(f'   Total processed: {count}')
    print(f'   ✅ Successfully labeled: {success_count}')
    print(f'   ⏭️  Skipped (too short): {skip_count}')
    print(f'   ❌ Errors: {error_count}')
    
    return


default_args = {
    "owner": "khangpt",
    "start_date": datetime(2024, 1, 18),
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


dag = DAG(
    DAG_NAME,
    default_args=default_args,
    description="Label newly crawled articles with LLM sentiment (runs 10min after CMC crawler)",
    schedule_interval="10 * * * *",  # Every hour at :10 (10 minutes after CMC crawler)
    catchup=False,
    max_active_runs=1,
    tags=["sentiment", "llm", "labeling", "gemini"],
)

label_task = PythonOperator(
    task_id=TASK_LABEL_SENTIMENT,
    python_callable=label_new_articles,
    dag=dag,
)

label_task

