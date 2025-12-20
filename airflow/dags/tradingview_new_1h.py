"""
TradingView Ideas Crawler DAG
Fetches cryptocurrency trading ideas from TradingView every hour
"""
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

from crawler.tradingview import TradingViewCrawler
from database.mongodb import MongoManager
from database.kafka import Kafka

DAG_NAME = os.path.basename(__file__)
COLLECTION_NAME = "tradingview_ideas"
KAFKA_TOPIC = "tradingview-ideas"


def crawl_tradingview_ideas():
    """
    Main task: Crawl TradingView ideas and save to MongoDB
    """
    try:
        print("\n" + "="*60)
        print(f"🚀 Starting TradingView Ideas Crawler at {datetime.now()}")
        print("="*60)
        
        # Initialize services
        mongo_client = MongoManager('blog-data')
        kafka = Kafka()
        
        # Initialize crawler
        crawler = TradingViewCrawler(max_ideas_per_symbol=10)
        
        # Fetch all crypto ideas
        all_ideas = crawler.fetch_all_crypto_ideas()
        
        if not all_ideas:
            print("⚠️  No ideas fetched")
            return
        
        print(f"\n💾 Saving {len(all_ideas)} ideas to MongoDB...")
        
        # Save to MongoDB
        inserted_ids, hash_ids, error_ids = mongo_client.insert_many(
            collection_name=COLLECTION_NAME,
            data=all_ideas,
            ordered=False
        )
        
        print(f"✅ Successfully saved {len(hash_ids)} new ideas")
        print(f"📊 Duplicate ideas skipped: {len(error_ids)}")
        
        # Push to Kafka for sentiment analysis
        if hash_ids:
            print(f"\n📨 Pushing {len(hash_ids)} ideas to Kafka topic: {KAFKA_TOPIC}")
            
            # Send in chunks of 10
            chunk_size = 10
            for i in range(0, len(hash_ids), chunk_size):
                chunk = hash_ids[i:i + chunk_size]
                message = {"hash_ids": chunk, "source": "tradingview"}
                kafka.producer_send(KAFKA_TOPIC, message)
                print(f"   ✅ Pushed chunk: {chunk}")
        
        print("\n" + "="*60)
        print("✅ TradingView crawler completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error in TradingView crawler: {e}")
        raise


# DAG configuration
default_args = {
    'owner': 'khangpt',
    'start_date': datetime(2025, 11, 19),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'tradingview_ideas_1h',
    default_args=default_args,
    description='Crawl TradingView cryptocurrency ideas every hour',
    schedule_interval='0 * * * *',  # Every hour at minute 0
    catchup=False,
    tags=['sentiman', 'tradingview', 'crypto'],
    max_active_runs=1,
)

# Define task
task_crawl_tradingview = PythonOperator(
    task_id='crawl_tradingview_ideas',
    python_callable=crawl_tradingview_ideas,
    dag=dag,
)

task_crawl_tradingview

