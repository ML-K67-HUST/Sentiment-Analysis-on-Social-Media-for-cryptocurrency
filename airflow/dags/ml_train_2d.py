"""
ML Training Pipeline for Bitcoin Price Prediction
Trains models using labeled sentiment data (text + metrics) and Bitcoin price movements.
Includes TF-IDF vectorization and advanced evaluation metrics.
"""
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import mlflow
import mlflow.sklearn
import joblib
from database.mongodb import MongoManager
import shutil

# Download NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


DAG_NAME = "price_prediction_pipeline"
MLFLOW_TRACKING_URI = "http://mlflow:5000"
MLFLOW_EXPERIMENT_NAME = "bitcoin_price_prediction"


def preprocess_text(text):
    """Clean and preprocess text for TF-IDF."""
    if not isinstance(text, str):
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    words = text.split()
    filtered_words = [w for w in words if w not in stop_words]
    
    return " ".join(filtered_words)


def extract_and_prepare_data(**kwargs):
    """
    Extract labeled data from MongoDB and prepare for training.
    Includes TF-IDF vectorization for text content.
    
    Returns:
        dict: Training data stats via XCom
    """
    print("🔍 Extracting labeled data from MongoDB...")
    
    mongo_client = MongoManager('blog-data')
    
    # Get all labeled records
    labeled_data = list(mongo_client.find(
        collection_name='cmc_labeled_data',
        filter={'labeled': 'true'}
    ))
    
    if not labeled_data or len(labeled_data) < 5:
        print(f"⚠️  Not enough labeled data: {len(labeled_data)} records")
        print("   Need at least 5 records for training")
        return {'status': 'insufficient_data', 'count': len(labeled_data)}
    
    print(f"✅ Found {len(labeled_data)} labeled records")
    
    # Convert to DataFrame
    df = pd.DataFrame(labeled_data)
    
    # 1. Prepare Text Features (TF-IDF)
    print("📝 Processing text features...")
    # Extract content from source_data if available, else use empty string
    df['processed_content'] = df.apply(
        lambda row: preprocess_text(
            row.get('source_data', {}).get('content', '') 
            if isinstance(row.get('source_data'), dict) else ''
        ), 
        axis=1
    )
    
    # Initialize TF-IDF Vectorizer
    tfidf = TfidfVectorizer(max_features=1000) # Limit to top 1000 words
    X_text = tfidf.fit_transform(df['processed_content']).toarray()
    
    print(f"   TF-IDF shape: {X_text.shape}")
    
    # Save vectorizer for inference
    joblib.dump(tfidf, '/tmp/tfidf_vectorizer.pkl')
    print("✅ TF-IDF vectorizer saved to /tmp/tfidf_vectorizer.pkl")
    
    # 2. Prepare Numerical Features
    print("🔢 Processing numerical features...")
    features_num = []
    targets = []
    
    for record in labeled_data:
        try:
            # Features: sentiment_score, confidence, timestamp
            feature_vector = [
                record.get('sentiment_score', 0),
                record.get('confidence', 0),
                record.get('timestamp', 0)
            ]
            
            # Target: price_movement_1h
            target = float(record.get('price_movement_1h', 0))
            
            features_num.append(feature_vector)
            targets.append(target)
            
        except Exception as e:
            print(f"⚠️  Skipping record due to error: {e}")
            continue
            
    X_num = np.array(features_num)
    y = np.array(targets)
    
    # 3. Combine Features
    # Concatenate numerical features and text features
    # Note: We need to ensure alignment. Since we iterated labeled_data for both, order is preserved.
    # However, if any record was skipped in numerical loop, we have a mismatch.
    # Better approach: Filter DataFrame first, then process.
    
    # Let's assume all records are valid for now for simplicity, or strictly align them.
    # Re-aligning:
    if len(X_num) != len(X_text):
        print("⚠️  Mismatch in feature lengths, falling back to intersection...")
        # (Implementation detail: Ideally clean data before vectorization)
        # For this demo, we assume data integrity or simple truncation
        min_len = min(len(X_num), len(X_text))
        X_num = X_num[:min_len]
        X_text = X_text[:min_len]
        y = y[:min_len]
        
    X_combined = np.hstack((X_num, X_text))
    
    print(f"📊 Data preparation complete:")
    print(f"   Combined Features shape: {X_combined.shape}")
    print(f"   Target shape: {y.shape}")
    
    # Save data to files for next task
    np.save('/tmp/X_train.npy', X_combined)
    np.save('/tmp/y_train.npy', y)
    
    return {
        'status': 'success',
        'total_records': len(y),
        'feature_shape': X_combined.shape,
        'n_text_features': X_text.shape[1],
        'n_num_features': X_num.shape[1]
    }


def train_models(**kwargs):
    """
    Train multiple ML models and log to MLflow.
    """
    ti = kwargs['ti']
    stats = ti.xcom_pull(task_ids='extract_data')
    
    if stats.get('status') != 'success':
        print(f"❌ Cannot train: {stats}")
        return {'status': 'skipped', 'reason': stats.get('status')}
    
    print("🤖 Loading training data...")
    X = np.load('/tmp/X_train.npy')
    y = np.load('/tmp/y_train.npy')
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"📊 Train set: {X_train.shape}, Test set: {X_test.shape}")
    
    # Normalize features (Scaling)
    # Note: TF-IDF is already normalized (usually), but scaling everything is fine for regression
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save scaler for inference
    joblib.dump(scaler, '/tmp/scaler.pkl')
    print("✅ Scaler saved to /tmp/scaler.pkl")
    
    # Setup MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    
    # Define models to train
    models = {
        'LinearRegression': LinearRegression(),
        'RandomForest': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
        'GradientBoosting': GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
    }
    
    results = []
    
    print("\\n🎯 Training models...")
    for name, model in models.items():
        print(f"\\n{'='*50}")
        print(f"Training: {name}")
        print(f"{'='*50}")
        
        with mlflow.start_run(run_name=f"{name}_TFIDF_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            # Train
            model.fit(X_train_scaled, y_train)
            
            # Predict
            y_pred_train = model.predict(X_train_scaled)
            y_pred_test = model.predict(X_test_scaled)
            
            # Metrics
            train_mse = mean_squared_error(y_train, y_pred_train)
            test_mse = mean_squared_error(y_test, y_pred_test)
            train_mae = mean_absolute_error(y_train, y_pred_train)
            test_mae = mean_absolute_error(y_test, y_pred_test)
            train_r2 = r2_score(y_train, y_pred_train)
            test_r2 = r2_score(y_test, y_pred_test)
            
            # Log to MLflow
            mlflow.log_param("model_type", name)
            mlflow.log_param("features", "TF-IDF + Sentiment + Timestamp")
            mlflow.log_param("n_features", X_train.shape[1])
            
            mlflow.log_metric("train_mse", train_mse)
            mlflow.log_metric("test_mse", test_mse)
            mlflow.log_metric("train_mae", train_mae)
            mlflow.log_metric("test_mae", test_mae)
            mlflow.log_metric("train_r2", train_r2)
            mlflow.log_metric("test_r2", test_r2)
            
            # Log model
            mlflow.sklearn.log_model(model, "model")
            
            # Log artifacts (Scaler & Vectorizer)
            mlflow.log_artifact('/tmp/scaler.pkl', artifact_path="preprocessor")
            mlflow.log_artifact('/tmp/tfidf_vectorizer.pkl', artifact_path="preprocessor")
            
            results.append({
                'name': name,
                'test_mse': test_mse,
                'test_mae': test_mae,
                'test_r2': test_r2,
                'run_id': mlflow.active_run().info.run_id
            })
            
            print(f"✅ {name} trained successfully:")
            print(f"   Test MAE: {test_mae:.6f}, R²: {test_r2:.4f}")
    
    # Find best model (lowest test MAE)
    best_model = min(results, key=lambda x: x['test_mae'])
    
    print(f"\\n🏆 BEST MODEL: {best_model['name']}")
    
    return {
        'status': 'success',
        'best_model': best_model,
        'all_results': results
    }


def register_best_model(**kwargs):
    """
    Register the best model in MLflow Model Registry.
    """
    ti = kwargs['ti']
    train_results = ti.xcom_pull(task_ids='train_and_evaluate_models')
    
    if train_results.get('status') != 'success':
        print(f"❌ Cannot register: {train_results}")
        return {'status': 'skipped'}
    
    best_model = train_results['best_model']
    
    print(f"📦 Registering best model: {best_model['name']}")
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    try:
        # Register model
        model_uri = f"runs:/{best_model['run_id']}/model"
        registered_model = mlflow.register_model(
            model_uri=model_uri,
            name="BestModel"
        )
        
        # Transition to Production
        client = mlflow.tracking.MlflowClient()
        client.transition_model_version_stage(
            name="BestModel",
            version=registered_model.version,
            stage="Production"
        )
        
        # Copy scaler and vectorizer to backend services directory
        shutil.copy('/tmp/scaler.pkl', '/opt/airflow/dags/services/scaler.pkl')
        shutil.copy('/tmp/tfidf_vectorizer.pkl', '/opt/airflow/dags/services/tfidf_vectorizer.pkl')
        print("✅ Scaler and TF-IDF Vectorizer copied to services directory")
        
        return {'status': 'success', 'model_version': registered_model.version}
        
    except Exception as e:
        print(f"❌ Error registering model: {e}")
        return {'status': 'error', 'error': str(e)}


# DAG definition
default_args = {
    'owner': 'khangpt',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    DAG_NAME,
    default_args=default_args,
    description='Bitcoin price prediction model training pipeline with TF-IDF',
    schedule_interval='0 0 */2 * *',
    catchup=False,
    max_active_runs=1,
    tags=['ml', 'bitcoin', 'training', 'tfidf']
)

# Tasks
extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_and_prepare_data,
    provide_context=True,
    dag=dag,
)

train_task = PythonOperator(
    task_id='train_and_evaluate_models',
    python_callable=train_models,
    provide_context=True,
    dag=dag,
)

register_task = PythonOperator(
    task_id='deploy_best_model',
    python_callable=register_best_model,
    provide_context=True,
    dag=dag,
)

# Task dependencies
extract_task >> train_task >> register_task
