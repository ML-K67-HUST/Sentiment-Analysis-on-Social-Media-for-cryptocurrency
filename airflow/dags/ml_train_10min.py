"""
Updated ML Training Pipeline - 30-Minute Aggregated Features
Trains models using aggregated features instead of individual articles
"""

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from database.mongodb import MongoManager
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import pandas as pd
import joblib
import os

DAG_NAME = "price_prediction_pipeline_10min_v2"
EXPERIMENT_NAME = "bitcoin_price_prediction_10min"

# Feature names (17 total)
FEATURE_COLS = [
    'num_articles',
    'llm_sentiment_avg', 
    'llm_confidence_avg',
    # NLP aggregated features (14)
    'avg_positive_word_ratio',
    'avg_negative_word_ratio',
    'avg_neutral_word_ratio',
    'avg_compound_score',
    'total_avg_sentence_length',
    'total_word_count',
    'avg_unique_word_ratio',
    'total_exclamation_count',
    'total_question_count',
    'total_btc_mention_count',
    'total_price_keyword_count',
    'avg_technical_term_ratio',
    'total_ne_person_count',
    'total_ne_org_count'
]


def extract_and_prepare_data(**context):
    """Extract labeled 10-min aggregated data and prepare features"""
    
    print("🔍 Extracting labeled 10-min aggregated data from MongoDB...")
    
    mongo = MongoManager('blog-data')
    
    labeled_data = list(mongo.find(
        collection_name='aggregated_features_10min',
        filter={'labeled': True}
    ))
    
    if not labeled_data or len(labeled_data) < 10:
        print(f"⚠️  Not enough labeled data: {len(labeled_data)} records")
        print("   Need at least 10 records for training")
        return {'status': 'insufficient_data', 'count': len(labeled_data)}
    
    print(f"✅ Found {len(labeled_data)} labeled records")
    
    # Prepare features
    features_list = []
    labels_list = []
    
    for record in labeled_data:
        try:
            nlp_agg = record.get('nlp_features_agg', {})
            
            # Build feature vector (17 features)
            features = [
                record.get('num_articles', 0),
                record.get('llm_sentiment_avg', 0.0),
                record.get('llm_confidence_avg', 0.0),
                # NLP features
                nlp_agg.get('avg_positive_word_ratio', 0.0),
                nlp_agg.get('avg_negative_word_ratio', 0.0),
                nlp_agg.get('avg_neutral_word_ratio', 0.0),
                nlp_agg.get('avg_compound_score', 0.0),
                nlp_agg.get('total_avg_sentence_length', 0.0),
                nlp_agg.get('total_word_count', 0),
                nlp_agg.get('avg_unique_word_ratio', 0.0),
                nlp_agg.get('total_exclamation_count', 0),
                nlp_agg.get('total_question_count', 0),
                nlp_agg.get('total_btc_mention_count', 0),
                nlp_agg.get('total_price_keyword_count', 0),
                nlp_agg.get('avg_technical_term_ratio', 0.0),
                nlp_agg.get('total_ne_person_count', 0),
                nlp_agg.get('total_ne_org_count', 0)
            ]
            
            features_list.append(features)
            labels_list.append(record.get('price_movement_10min', 0.0))
            
        except Exception as e:
            print(f"⚠️  Skipping record due to error: {e}")
            continue
    
    X = np.array(features_list)
    y = np.array(labels_list)
    
    print(f"✅ Prepared dataset: X shape={X.shape}, y shape={y.shape}")
    
    # Save to XCom
    context['ti'].xcom_push(key='X', value=X.tolist())
    context['ti'].xcom_push(key='y', value=y.tolist())
    context['ti'].xcom_push(key='num_samples', value=len(X))
    
    return {'status': 'success', 'num_samples': len(X)}


def train_models(**context):
    """Train multiple regression models and log to MLflow"""
    
    # Get data from XCom
    X = np.array(context['ti'].xcom_pull(key='X', task_ids='extract_data'))
    y = np.array(context['ti'].xcom_pull(key='y', task_ids='extract_data'))
    
    print(f"🤖 Training models on {len(X)} samples with {X.shape[1]} features...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save scaler
    os.makedirs('/tmp', exist_ok=True)
    joblib.dump(scaler, '/tmp/scaler.pkl')
    print("✅ Scaler saved to /tmp/scaler.pkl")
    
    # Set MLflow experiment
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    # Train models
    models = {
        'LinearRegression': LinearRegression(),
        'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42),
        'GradientBoosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
    }
    
    results = []
    
    for name, model in models.items():
        with mlflow.start_run(run_name=f"{name}_{datetime.now().strftime('%Y%m%d_%H%M')}"):
            print(f"\n🔧 Training {name}...")
            
            # Train
            model.fit(X_train_scaled, y_train)
            
            # Predict
            y_pred = model.predict(X_test_scaled)
            
            # Evaluate
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            print(f"   MAE: {mae:.4f}")
            print(f"   MSE: {mse:.4f}")
            print(f"   R²:  {r2:.4f}")
            
            # Log to MLflow
            mlflow.log_param("model_type", name)
            mlflow.log_param("n_samples", len(X))
            mlflow.log_param("n_features", X.shape[1])
            mlflow.log_metric("mae", mae)
            mlflow.log_metric("mse", mse)
            mlflow.log_metric("r2_score", r2)
            
            # Log model
            mlflow.sklearn.log_model(model, "model")
            
            # Log scaler
            mlflow.log_artifact('/tmp/scaler.pkl')
            
            results.append({
                'name': name,
                'mae': mae,
                'run_id': mlflow.active_run().info.run_id
            })
    
    # Find best model
    best_result = min(results, key=lambda x: x['mae'])
    
    print(f"\n🏆 Best model: {best_result['name']} with MAE={best_result['mae']:.4f}")
    
    context['ti'].xcom_push(key='best_run_id', value=best_result['run_id'])
    context['ti'].xcom_push(key='best_model_name', value=best_result['name'])
    
    return best_result


def register_best_model(**context):
    """Register best model to MLflow Model Registry"""
    
    best_run_id = context['ti'].xcom_pull(key='best_run_id', task_ids='train_and_evaluate_models')
    best_model_name = context['ti'].xcom_pull(key='best_model_name', task_ids='train_and_evaluate_models')
    
    print(f"📦 Registering best model: {best_model_name} (run_id={best_run_id})")
    
    model_uri = f"runs:/{best_run_id}/model"
    model_name = "BestModel_10min"
    
    # Register model
    model_details = mlflow.register_model(model_uri, model_name)
    
    # Transition to Production
    client = mlflow.tracking.MlflowClient()
    client.transition_model_version_stage(
        name=model_name,
        version=model_details.version,
        stage="Production"
    )
    
    print(f"✅ Model registered as {model_name} version {model_details.version} in Production stage")
    
    # Copy scaler to services directory
    os.makedirs('/opt/airflow/dags/services', exist_ok=True)
    import shutil
    shutil.copy('/tmp/scaler.pkl', '/opt/airflow/dags/services/scaler_10min.pkl')
    
    print("✅ Scaler copied to /opt/airflow/dags/services/scaler_10min.pkl")
    
    return model_details.version


default_args = {
    "owner": "khangpt",
    "start_date": datetime(2024, 1, 18),
    "depends_on_past": False,
}

dag = DAG(
    DAG_NAME,
    default_args=default_args,
    description="ML training pipeline using 10-min aggregated features",
    schedule_interval="0 0 */2 * *",  # Every 2 days at midnight
    catchup=False,
    max_active_runs=1,
    tags=["ml", "training", "aggregation"],
)

extract_task = PythonOperator(
    task_id="extract_data",
    python_callable=extract_and_prepare_data,
    provide_context=True,
    dag=dag,
)

train_task = PythonOperator(
    task_id="train_and_evaluate_models",
    python_callable=train_models,
    provide_context=True,
    dag=dag,
)

register_task = PythonOperator(
    task_id="register_best_model",
    python_callable=register_best_model,
    provide_context=True,
    dag=dag,
)

extract_task >> train_task >> register_task
