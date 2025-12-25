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
    x_data = context['ti'].xcom_pull(key='X', task_ids='extract_data')
    y_data = context['ti'].xcom_pull(key='y', task_ids='extract_data')
    
    if not x_data or not y_data:
        print("⚠️ No data received from extract_data task. Skipping training.")
        return "skipped"
    
    X = np.array(x_data)
    y = np.array(y_data)
    
    print(f"🤖 Training models on {len(X)} samples with {X.shape[1]} features...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # --- SUBMISSION REQUIREMENT: Save Dataset Splits ---
    print("💾 Saving dataset splits for submission...")
    df_train = pd.DataFrame(X_train, columns=FEATURE_COLS)
    df_train['target'] = y_train
    
    df_test = pd.DataFrame(X_test, columns=FEATURE_COLS)
    df_test['target'] = y_test
    
    os.makedirs('/tmp/submission_data', exist_ok=True)
    train_path = '/tmp/submission_data/train_set.csv'
    test_path = '/tmp/submission_data/test_set.csv'
    
    df_train.to_csv(train_path, index=False)
    df_test.to_csv(test_path, index=False)
    print(f"✅ Saved train_set.csv ({len(df_train)}) and test_set.csv ({len(df_test)})")
    # ----------------------------------------------------
    
    # Scale features
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save scaler
    os.makedirs('/tmp', exist_ok=True)
    joblib.dump(scaler, '/tmp/scaler.pkl')
    print("✅ Scaler saved to /tmp/scaler.pkl")
    
    # Set MLflow tracking URI
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    
    # Set MLflow experiment
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    # Import for Learning Curve & Tuning
    from sklearn.model_selection import learning_curve, GridSearchCV
    from sklearn.dummy import DummyRegressor
    import matplotlib.pyplot as plt
    try:
        import wandb
    except ImportError:
        wandb = None
        print("⚠️ WandB not found. Skipping WandB logging.")

    # Define models with parameter grids for tuning
    # We only tune Random Forest to save time, others use defaults
    models_config = {
        'Baseline_Dummy': {
            'model': DummyRegressor(strategy='mean'),
            'params': {}
        },
        'LinearRegression': {
            'model': LinearRegression(),
            'params': {}
        },
        'RandomForest': {
            'model': RandomForestRegressor(random_state=42),
            'params': {
                'n_estimators': [50, 100],
                'max_depth': [None, 10, 20],
                'min_samples_split': [2, 5]
            }
        },
        'GradientBoosting': {
            'model': GradientBoostingRegressor(random_state=42),
            'params': {
                'n_estimators': [100],
                'learning_rate': [0.1],
                'max_depth': [3]
            }
        }
    }
    
    results = []
    
    # Initialize WandB Run (Global for this DAG run, or per model? Let's do per model or 1 run)
    # Using 1 WandB run for the whole experiment to compare models in one dashboard is better, 
    # but MLflow logic loops. Let's start a WandB run at start.
    if wandb:
        try:
            wandb.login(key=os.getenv("WANDB_API_KEY"))
            run = wandb.init(project="bitcoin_price_prediction_10min", reinit=True, name=f"run_{datetime.now().strftime('%Y%m%d_%H%M')}")
        except Exception as e:
            print(f"⚠️ WandB Init Failed: {e}")
            wandb = None

    for name, config in models_config.items():
        with mlflow.start_run(run_name=f"{name}_{datetime.now().strftime('%Y%m%d_%H%M')}"):
            print(f"\n🔧 Training {name}...")
            
            base_model = config['model']
            param_grid = config['params']
            
            # --- FEATURE: Hyperparameter Tuning (GridSearch) ---
            if param_grid:
                print(f"   🔎 Tuning hyperparameters for {name}...")
                grid_search = GridSearchCV(base_model, param_grid, cv=3, scoring='neg_mean_absolute_error', n_jobs=-1)
                grid_search.fit(X_train_scaled, y_train)
                
                best_model = grid_search.best_estimator_
                best_params = grid_search.best_params_
                print(f"   ✨ Best Params: {best_params}")
                
                # Log best params
                for param, value in best_params.items():
                    mlflow.log_param(f"best_{param}", value)
                    if wandb: wandb.log({f"{name}_best_{param}": value})
            else:
                best_model = base_model
                best_model.fit(X_train_scaled, y_train)
                best_params = {}
            # ----------------------------------------------------
            
            # Predict
            y_pred = best_model.predict(X_test_scaled)
            
            # Evaluate
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            print(f"   MAE: {mae:.4f}")
            print(f"   MSE: {mse:.4f}")
            print(f"   R²:  {r2:.4f}")
            
            # --- SUBMISSION REQUIREMENT: Generate Learning Curve ---
            print(f"📊 Generating Learning Curve for {name}...")
            try:
                train_sizes, train_scores, test_scores = learning_curve(
                    best_model, X_train_scaled, y_train, cv=5, scoring='neg_mean_absolute_error',
                    n_jobs=-1, train_sizes=np.linspace(0.1, 1.0, 5)
                )
                
                train_scores_mean = -np.mean(train_scores, axis=1)
                test_scores_mean = -np.mean(test_scores, axis=1)

                plt.figure()
                plt.title(f"Learning Curve: {name}")
                plt.xlabel("Training examples")
                plt.ylabel("MAE Score (Lower is better)")
                plt.grid()
                
                plt.plot(train_sizes, train_scores_mean, 'o-', color="r", label="Training score")
                plt.plot(train_sizes, test_scores_mean, 'o-', color="g", label="Cross-validation score")
                
                plt.legend(loc="best")
                plot_path = f'/tmp/submission_data/learning_curve_{name}.png'
                plt.savefig(plot_path)
                plt.close()
                print(f"✅ Saved Learning Curve plot to {plot_path}")
                mlflow.log_artifact(plot_path)
                
                # Log to WandB
                if wandb:
                    wandb.log({f"{name}_learning_curve": wandb.Image(plot_path)})
                    
                    # Log metrics
                    wandb.log({
                        f"{name}_mae": mae,
                        f"{name}_mse": mse,
                        f"{name}_r2": r2
                    })
                
            except Exception as e:
                print(f"⚠️ Failed to generate learning curve: {e}")
            # --------------------------------------------------------

            # Log to MLflow
            mlflow.log_param("model_type", name)
            mlflow.log_param("n_samples", len(X))
            mlflow.log_param("n_features", X.shape[1])
            mlflow.log_metric("mae", mae)
            mlflow.log_metric("mse", mse)
            mlflow.log_metric("r2_score", r2)
            
            # Log model
            mlflow.sklearn.log_model(best_model, "model")
            
            # Log scaler
            mlflow.log_artifact('/tmp/scaler.pkl')
            
            # Log Datasets
            mlflow.log_artifact(train_path)
            mlflow.log_artifact(test_path)
            
            results.append({
                'name': name,
                'mae': mae,
                'run_id': mlflow.active_run().info.run_id
            })
    
    
    # ... (Previous imports)
    
    # Import TensorFlow for LSTM
    try:
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        print(f"✅ TensorFlow {tf.__version__} imported")
        HAS_TF = True
    except ImportError:
        print("⚠️ TensorFlow not found. LSTM will be skipped.")
        HAS_TF = False
        
    # Helper to prepare sequences for LSTM
    def create_sequences(X_data, y_data, time_steps=6):
        Xs, ys = [], []
        for i in range(len(X_data) - time_steps):
            Xs.append(X_data[i:(i + time_steps)])
            ys.append(y_data[i + time_steps])
        return np.array(Xs), np.array(ys)

    # ... (Inside train_models loop)

    
    if wandb:
        wandb.finish()

    # Find best model
    best_result = min(results, key=lambda x: x['mae'])
    
    print(f"\n🏆 Best model: {best_result['name']} with MAE={best_result['mae']:.4f}")
    
    context['ti'].xcom_push(key='best_run_id', value=best_result['run_id'])
    context['ti'].xcom_push(key='best_model_name', value=best_result['name'])
    
    return best_result


def register_best_model(**context):
    """Register best model to MLflow Model Registry"""
    
    # Set MLflow tracking URI explicitly
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    
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
