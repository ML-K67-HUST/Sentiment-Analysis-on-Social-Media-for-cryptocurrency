
import os
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import mlflow
import mlflow.sklearn
import joblib

# Constants
DATA_PATH = "sentiman_labeled_data.csv"
SCALER_PATH = "backend/services/scaler_10min.pkl"
MLFLOW_URI = "http://localhost:5001"  # Or http://mlflow:5000 if inside docker
EXPERIMENT_NAME = "crypto_price_prediction_10min"
REGISTERED_MODEL_NAME = "BestModel_10min"

def load_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data file ({DATA_PATH}) not found. Please run fix_and_push.py first.")
    
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} samples from {DATA_PATH}")
    return df

def prepare_data(df):
    # Features matching ml_api.py (17 features)
    feature_cols = [
        'num_articles',
        'llm_sentiment_avg',
        'llm_confidence_avg',
        'nlp_features_agg.avg_positive_word_ratio',
        'nlp_features_agg.avg_negative_word_ratio',
        'nlp_features_agg.avg_neutral_word_ratio',
        'nlp_features_agg.avg_compound_score',
        'nlp_features_agg.total_avg_sentence_length',
        'nlp_features_agg.total_word_count',
        'nlp_features_agg.avg_unique_word_ratio',
        'nlp_features_agg.total_exclamation_count',
        'nlp_features_agg.total_question_count',
        'nlp_features_agg.total_btc_mention_count',
        'nlp_features_agg.total_price_keyword_count',
        'nlp_features_agg.avg_technical_term_ratio',
        'nlp_features_agg.total_ne_person_count',
        'nlp_features_agg.total_ne_org_count'
    ]
    
    target_col = 'price_movement_10min'  # Regression target
    
    # Check if target exists, if not derive it from btc_price if possible, else fail
    if target_col not in df.columns:
        if 'btc_price' in df.columns:
            # We cannot easily derive 10min movement from single rows without time-series context
            # But the dataset usually has it. If missing, maybe calc dummy?
            print(f"Warning: {target_col} missing. Using btc_price as proxy (Not ideal).")
            target_col = 'btc_price'
        else:
            raise ValueError(f"Target column {target_col} not found.")

    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    # Fill NAs
    X = X.fillna(0)
    y = y.fillna(0)
    
    return X, y, feature_cols

def train_and_log():
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    # 1. Load & Prepare
    try:
        df = load_data()
    except Exception:
        # Fallback for dev if csv missing
        print("CSV not found, skipping training execution logic check.")
        return

    X, y, feature_names = prepare_data(df)
    
    # 2. Scale
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Save Scaler for API
    os.makedirs(os.path.dirname(SCALER_PATH), exist_ok=True)
    joblib.dump(scaler, SCALER_PATH)
    print(f"Saved scaler to {SCALER_PATH}")
    
    # 3. Split
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    
    models = {
        "RandomForest": RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
        "LinearRegression": LinearRegression()
    }
    
    best_mse = float('inf')
    best_model = None
    best_model_name = ""
    
    for name, model in models.items():
        with mlflow.start_run(run_name=f"{name}_{datetime.now().strftime('%H%M')}"):
            print(f"Training {name}...")
            model.fit(X_train, y_train)
            
            preds = model.predict(X_test)
            
            # Metrics
            mse = mean_squared_error(y_test, preds)
            mae = mean_absolute_error(y_test, preds)
            r2 = r2_score(y_test, preds)
            
            mlflow.log_metrics({"mse": mse, "mae": mae, "r2": r2})
            mlflow.log_params(model.get_params())
            
            # Log Model
            mlflow.sklearn.log_model(model, "model")
            
            print(f"  MSE: {mse:.6f}, MAE: {mae:.6f}, R2: {r2:.4f}")
            
            if mse < best_mse:
                best_mse = mse
                best_model = model
                best_model_name = name

    # Register Best Model
    if best_model:
        print(f"\n🏆 Best Model: {best_model_name} (MSE: {best_mse:.6f})")
        
        # Log best model again as a distinct run to be the 'Production' candidate
        with mlflow.start_run(run_name=f"BEST_{best_model_name}") as run:
            mlflow.log_metrics({"mse": best_mse})
            mlflow.sklearn.log_model(
                best_model, 
                "model",
                registered_model_name=REGISTERED_MODEL_NAME
            )
            print(f"Registered {REGISTERED_MODEL_NAME} version.")

if __name__ == "__main__":
    train_and_log()