from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from airflow.models import Variable
import time

DAG_NAME = "ml_train_2d"
TASK_CRAWL_CMC_NEWS = "automatically_train_and_deploy_model_for_each_2d"
def extract_data(**kwargs):
    # Giả sử bạn trả về dữ liệu cần truyền đi
    data = {'feature1': [1, 2, 3], 'feature2': [4, 5, 6]}
    return data  # Dữ liệu này được lưu vào XCom

def train_and_evaluate_models(ti, **kwargs):
    # Lấy dữ liệu từ task trước thông qua XCom
    extracted_data = ti.xcom_pull(task_ids='extract_data')
    print("Data for training:", extracted_data)
    model_results = {'model_name': 'model_v1', 'accuracy': 0.95}
    return model_results

def deploy_best_model(ti, **kwargs):
    # Lấy kết quả training từ XCom
    model_results = ti.xcom_pull(task_ids='train_and_evaluate_models')
    print("Deploying:", model_results)

default_args = {
    'owner': 'khangptt',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'price_prediction_pipeline',
    default_args=default_args,
    description='Weekly price prediction model training and deployment pipeline',
    schedule_interval='@weekly',
    catchup=False
)

extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    provide_context=True,
    dag=dag,
)

train_evaluate_task = PythonOperator(
    task_id='train_and_evaluate_models',
    python_callable=train_and_evaluate_models,
    provide_context=True,
    dag=dag,
)

deploy_task = PythonOperator(
    task_id='deploy_best_model',
    python_callable=deploy_best_model,
    provide_context=True,
    dag=dag,
)

extract_task >> train_evaluate_task >> deploy_task
