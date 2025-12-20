"""
Label 30-Minute Aggregated Features
Fetches Bitcoin price movement 30 minutes after each aggregated window
"""

from database.mongodb import MongoManager
from datetime import datetime, timedelta
from utils.data_constructor import get_bitcoin_price_one_hour
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import requests
import json

DAG_NAME = "label_10min_aggregated_data"
TASK_LABELLING = "labelling_10min_batches"


def get_bitcoin_price_at_timestamp(timestamp):
    """Get Bitcoin price at specific timestamp using CoinRanking API"""
    headers = {
        'x-access-token': 'coinranking20b7cf109bbe9e42388a3faf8fe62f8ddda36dd7ec8a9f1f',
    }
    response = requests.get(
        f"https://api.coinranking.com/v2/coin/Qwsogvtv82FCd/price?timestamp={timestamp}",
        headers=headers,
        timeout=10
    )
    return response.text


def get_bitcoin_price_movement_10min(window_start_ts):
    """
    Calculate Bitcoin price movement 10 minutes after window start
    
    Args:
        window_start_ts: Unix timestamp of window start
    
    Returns:
        Percentage change (e.g., 0.5 for +0.5%, -1.2 for -1.2%)
        None if price data unavailable
    """
    try:
        # Window start time
        start_ts = str(int(window_start_ts))
        # 10 minutes later
        end_ts = str(int(window_start_ts) + 600)  # 600 seconds = 10 min
        
        # Get prices
        start_price_data = json.loads(get_bitcoin_price_at_timestamp(start_ts))
        end_price_data = json.loads(get_bitcoin_price_at_timestamp(end_ts))
        
        start_price = float(start_price_data['data']['price'])
        end_price = float(end_price_data['data']['price'])
        
        # Calculate percentage change
        price_movement = ((end_price - start_price) / start_price) * 100
        
        return price_movement
        
    except Exception as e:
        print(f"Error getting price movement: {e}")
        return None


def label():
    """
    Label unlabeled 10-min aggregations with Bitcoin price movement
    
    Process:
    1. Find unlabeled aggregations older than 10 minutes
    2. Get Bitcoin price 10 minutes after window start
    3. Calculate price movement percentage
    4. Update record with label
    """
    mongo_client = MongoManager('blog-data')
    
    # Find aggregations ready for labeling (older than 10 minutes)
    time_threshold = datetime.utcnow() - timedelta(minutes=10)
    
    filter_condition = {
        "window_start": {"$lt": time_threshold.timestamp()},
        "labeled": False,
        "aggregation_status": "complete"
    }
    
    print(f'🔍 Looking for unlabeled aggregations older than {time_threshold}...')
    print(f'Filter: {filter_condition}')
    
    matching_records = mongo_client.find(
        collection_name="aggregated_features_10min",
        filter=filter_condition,
    )
    
    if not matching_records:
        print('✅ NO BATCHES TO LABEL - All aggregations are labeled or not ready yet')
        return
    
    count = 0
    success_count = 0
    
    for record in matching_records:
        count += 1
        window_start = record.get('window_start')
        window_datetime = record.get('window_datetime', 'Unknown')
        num_articles = record.get('num_articles', 0)
        
        print(f'\n📊 Processing aggregation {count}')
        print(f'   Window: {window_datetime}')
        
        try:
            # Get Bitcoin price movement 10 minutes later
            price_movement = get_bitcoin_price_movement_10min(window_start)
            
            if price_movement is None:
                continue
            
            # Update with label
            mongo_client.update_one(
                collection_name='aggregated_features_10min',
                filter={'window_start': window_start},
                data={'$set': {
                    'labeled': True,
                    'price_movement_10min': price_movement,
                    'labeled_at': datetime.utcnow().timestamp()
                }}
            )
            
            success_count += 1
            print(f'✅ Labeled successfully!')
            print(f'   Price movement (10min): {price_movement:+.4f}%')
            
        except Exception as e:
            print(f'❌ Failed to label window {window_datetime}: {e}')
    
    return


default_args = {
    "owner": "khangpt",
    "start_date": datetime(2024, 1, 18),
    "depends_on_past": False,
}

dag = DAG(
    DAG_NAME,
    default_args=default_args,
    description="Label 10-min aggregated features with Bitcoin price movements",
    schedule_interval="5,15,25,35,45,55 * * * *",  # Run 5 min after every 10 min window
    catchup=False,
    max_active_runs=1,
    tags=["labeling", "aggregation", "bitcoin"],
)

label_task = PythonOperator(
    task_id=TASK_LABELLING,
    python_callable=label,
    dag=dag,
)

label_task
