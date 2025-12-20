from database.mongodb import MongoManager
from datetime import datetime, timedelta
from utils.data_constructor import get_bitcoin_price_one_hour
from airflow import DAG
from airflow.operators.python_operator import PythonOperator


DAG_NAME = "label_data"
TASK_LABELLING_DATA = "labelling_data_for_each_2h"

def label():
    """
    Label unlabeled sentiment data with Bitcoin price movement after 1 hour.
    
    Process:
    1. Find unlabeled records older than 1 hour
    2. Get Bitcoin price 1 hour after the article timestamp
    3. Mark as labeled and store in cmc_labeled_data collection
    4. Update original record to labeled='true'
    """
    mongo_client = MongoManager('blog-data')
    time_threshold = datetime.utcnow() - timedelta(hours=1)
    
    filter_condition = {
        "timestamp": {"$lt": time_threshold.timestamp()},
        "labeled": "false"
    }
    
    print(f'🔍 Looking for unlabeled records older than {time_threshold}...')
    print(f'Filter: {filter_condition}')
    
    matching_records = mongo_client.find(
        collection_name="cmc_unlabeled_data",
        filter=filter_condition,
    )
    
    if not matching_records:
        print('✅ NO RECORD TO LABEL - All records are already labeled or not ready yet')
        print(f'Current UTC time: {datetime.utcnow()}')
        print(f'Time threshold: {time_threshold}')
        print(f'Records must be at least 1 hour old to get price movement data')
        return
    
    count = 0
    success_count = 0
    
    for record in matching_records:
        count += 1
        hash_id = record.get('hash_id')
        symbol = record.get('symbol', 'BTC')
        timestamp = record.get('timestamp')
        
        print(f'\\n📊 Processing record {count}: {hash_id}')
        print(f'   Symbol: {symbol}, Timestamp: {datetime.fromtimestamp(timestamp)}')
        
        try:
            # Get Bitcoin price 1 hour later
            # Convert timestamp to int first (MongoDB stores as float)
            timestamp_int = int(timestamp)
            price_movement = get_bitcoin_price_one_hour(str(timestamp_int))
            
            if price_movement is None:
                print(f'⚠️  Could not get price movement for {hash_id}, skipping...')
                continue
            
            # Create labeled record
            labeled_record = record.copy()
            labeled_record['labeled'] = "true"
            labeled_record['price_movement_1h'] = price_movement
            labeled_record['labeled_at'] = datetime.utcnow().timestamp()
            
            # Remove _id to avoid duplicate key error
            if '_id' in labeled_record:
                del labeled_record['_id']
            
            # Insert into labeled collection
            mongo_client.insert_one(
                collection_name='cmc_labeled_data',
                data=labeled_record
            )
            
            # Update original record to mark as labeled
            mongo_client.update_one(
                collection_name='cmc_unlabeled_data',
                filter={'hash_id': hash_id},
                data={'$set': {'labeled': 'true', 'labeled_at': datetime.utcnow().timestamp()}}
            )
            
            success_count += 1
            print(f'✅ Labeled successfully!')
            print(f'   Price movement 1h: ${price_movement}')
            
        except Exception as e:
            print(f'❌ Failed to label {hash_id}: {e}')
    
    print(f'\\n🎉 LABELING COMPLETE')
    print(f'   Total processed: {count}')
    print(f'   Successfully labeled: {success_count}')
    print(f'   Failed: {count - success_count}')
    
    return


default_args = {
    "owner": "khangpt",
    "start_date": datetime(2024, 1, 18),
    "depends_on_past": False,
}


dag = DAG(
    DAG_NAME,
    default_args=default_args,
    description="Label unlabeled sentiment data with Bitcoin price movements",
    schedule_interval="0 */2 * * *",  # Every 2 hours
    catchup=False,
    max_active_runs=1,
    tags=["sentiment", "labeling", "bitcoin"],
)

label_task = PythonOperator(
    task_id=TASK_LABELLING_DATA,
    python_callable=label,
    dag=dag,
)

label_task
