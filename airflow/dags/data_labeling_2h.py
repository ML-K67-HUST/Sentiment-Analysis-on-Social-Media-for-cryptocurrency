from database.mongodb import MongoManager
from datetime import datetime, timedelta
from utils.data_constructor import get_bitcoin_price_one_hour
from airflow import DAG
from airflow.operators.python_operator import PythonOperator


DAG_NAME = "label_data"
TASK_LABELLING_DATA = "labelling_data_for_each_2h"

def label():
    mongo_client = MongoManager('blog-data')
    time_threshold = datetime.utcnow() - timedelta(hours=1)
    
    # filter_condition = {
    #     "timestamp":{"$lt":time_threshold},
    #     "labeled":"false"
    # }
    filter_condition = {
        "timestamp":{"$lt":time_threshold.timestamp()},
        # "labeled":"false"
    }
    # update_operation = {"$set":{"labeled":"true", "movement_hour_ahead":}}
    # Query từ db unlabeled có timestamp từ 1 giờ trước
    # Gán nhãn movement 1 giờ sau
    # Insert data gán nhãn vào mongodb, collection 'labeled'
    matching_records = mongo_client.find(
        collection_name="cmc_unlabeled_data",
        filter=filter_condition,
    )
    if not matching_records:
        print('NO RECORD TO LABEL, ALL LABELED OR IT IS NOT READY FOR LABELLING')
        print('FILTER:\n')
        print(filter_condition)
        return
    for record in matching_records:
        record['labeled'] = "true"
        record['movement_hour_ahead'] = get_bitcoin_price_one_hour(str(record['timestamp']))
        try:
            mongo_client.update_many(
                filter={
                    "hash_id":record['hash_id']
                },
                data=record
            )
            print(f"LABELED SUCESSFULLY FOR ARTICLE HASH ID {record['hash_id']}")
        except Exception as e:
            print(f'Failed to labelling data: {e}')
        
    
    return


default_args = {
    "owner": "khangpt",
    "start_date": datetime(2024, 1, 18),
    "depends_on_past": False,
}


dag = DAG(
    DAG_NAME,
    default_args=default_args,
    description="labelling_data_for_each_2h",
    schedule_interval="0 */2 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["coinmarketcap", "article"],
)

fetch_newest_article = PythonOperator(
    task_id=TASK_LABELLING_DATA,
    python_callable=label,
    dag=dag,
)

fetch_newest_article
