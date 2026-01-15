
import os
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, learning_curve
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import mlflow
import mlflow.sklearn
import joblib
import wandb
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load env
load_dotenv()

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

def plot_learning_curve(model, X, y, name):
    try:
        train_sizes, train_scores, test_scores = learning_curve(
            model, X, y, cv=5, scoring='neg_mean_absolute_error',
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
        plot_path = f'learning_curve_{name}.png'
        plt.savefig(plot_path)
        plt.close()
        return plot_path
    except Exception as e:
        print(f"Failed to plot learning curve for {name}: {e}")
        return None

def train_and_log():
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    # Initialize WandB
    wandb_key = os.getenv("WANDB_API_KEY")
    if wandb_key:
        wandb.login(key=wandb_key)
        wandb.init(project=EXPERIMENT_NAME, name=f"run_{datetime.now().strftime('%Y%m%d_%H%M')}", reinit=True)
    else:
        print("⚠️ WANDB_API_KEY not found. Skipping WandB.")
    
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
    
    # 3. Split (Time-based split to prevent leakage)
    # Sort by time first
    if 'window_start' in df.columns:
        # Re-attach timestamp for sorting then drop it
        X['window_start'] = df['window_start']
        X = X.sort_values('window_start')
        # Re-align y
        y = y.loc[X.index]
        # Drop time col from features
        X = X.drop(columns=['window_start'])
    
    # Simple time-series split (no shuffle)
    # Time-series split: 70% Train, 15% Val, 15% Test
    n = len(X)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)
    
    X_train = X.iloc[:train_end]
    X_val = X.iloc[train_end:val_end]
    X_test = X.iloc[val_end:]
    
    y_train = y.iloc[:train_end]
    y_val = y.iloc[train_end:val_end]
    y_test = y.iloc[val_end:]
    
    print(f"Split sizes: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    
    # Define models
    
    # --- 1. Random Forest (Iterative) ---
    rf_name = "RandomForest"
    rf_params = {"n_estimators": 100, "max_depth": 10, "random_state": 42, "warm_start": True}
    rf_model = RandomForestRegressor(**rf_params)
    rf_model.n_estimators = 0
    
    best_mse = float('inf')
    best_model = None
    best_model_name = ""

    with mlflow.start_run(run_name=f"{rf_name}"):
        print(f"Training {rf_name} iteratively...")
        for i in range(1, 101):
            rf_model.n_estimators = i
            rf_model.fit(X_train, y_train)
            if wandb.run:
                # Log only every 5 steps to speed up if needed, but 100 is fine
                val_preds = rf_model.predict(X_val)
                train_preds = rf_model.predict(X_train)
                
                wandb.log({
                    f"{rf_name}_val_mse": mean_squared_error(y_val, val_preds), 
                    f"{rf_name}_val_mae": mean_absolute_error(y_val, val_preds),
                    f"{rf_name}_val_r2": r2_score(y_val, val_preds),
                    
                    f"{rf_name}_train_mse": mean_squared_error(y_train, train_preds), 
                    f"{rf_name}_train_mae": mean_absolute_error(y_train, train_preds),
                    f"{rf_name}_train_r2": r2_score(y_train, train_preds),
                    
                    "iteration": i
                })
        
        # Final Validation Metrics
        preds = rf_model.predict(X_val)
        mse = mean_squared_error(y_val, preds)
        mae = mean_absolute_error(y_val, preds)
        r2 = r2_score(y_val, preds)
        
        mlflow.log_metrics({"val_mse": mse, "val_mae": mae, "val_r2": r2})
        mlflow.sklearn.log_model(rf_model, "model")
        print(f"  {rf_name} - Val MSE: {mse:.6f}, Val R2: {r2:.4f}")
        
        if mse < best_mse:
            best_mse = mse
            best_model = rf_model
            best_model_name = rf_name

    # --- 2. XGBoost (Iterative) ---
    try:
        from xgboost import XGBRegressor
        xgb_name = "XGBoost"
        xgb_model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        
        with mlflow.start_run(run_name=f"{xgb_name}"):
            print(f"Training {xgb_name}...")
            # XGBoost allows extracting evaluation results per iteration if we provide eval_set
            xgb_model.fit(
                X_train, y_train, 
                eval_set=[(X_test, y_test)], 
                verbose=False
            )
            
            # Log history from xgb
            results = xgb_model.evals_result()
            # results['validation_0']['rmse'] (or default metric)
            # XGBoost default obj for reg is sq error -> rmse usually
            
            if wandb.run and results:
                # XGBoost default metric might be rmse
                # Let's just rely on final predict or manual loop if we want exact MAE/R2 per step
                # For speed let's just log the final, OR use staged loop?
                # XGBoost doesn't have warm_start quite like sklearn RF.
                # Let's allow standard fit and maybe log final point. 
                # User wants "dots". Let's do manual loop for XGB too!
                pass
        
        # Manual Loop for XGBoost "Dots"
        xgb_iter_model = XGBRegressor(n_estimators=1, learning_rate=0.1, max_depth=3, random_state=42)
        print(f"Training {xgb_name} iteratively for plotting...")
        
        # Incremental training
        for i in range(1, 101):
            xgb_iter_model.n_estimators = i
            # XGB requires reloading model to continue? No, just fit with new n_estimators? 
            # Actually XGB APIs are tricky for warm_start.
            # Simpler: fit new model with n_estimators=i (fast for small data)
            xgb_iter_model.fit(X_train, y_train)
            
            val_preds = xgb_iter_model.predict(X_val)
            train_preds = xgb_iter_model.predict(X_train)
            
            wandb.log({
                f"{xgb_name}_val_mse": mean_squared_error(y_val, val_preds), 
                f"{xgb_name}_val_mae": mean_absolute_error(y_val, val_preds),
                f"{xgb_name}_val_r2": r2_score(y_val, val_preds),
                
                f"{xgb_name}_train_mse": mean_squared_error(y_train, train_preds), 
                f"{xgb_name}_train_mae": mean_absolute_error(y_train, train_preds),
                f"{xgb_name}_train_r2": r2_score(y_train, train_preds),
                
                "iteration": i
            })
            
        preds = xgb_iter_model.predict(X_val)
        mse = mean_squared_error(y_val, preds)
        mae = mean_absolute_error(y_val, preds)
        r2 = r2_score(y_val, preds)
        
        print(f"  {xgb_name} - MSE: {mse:.6f}, R2: {r2:.4f}")
        
        if mse < best_mse:
            best_mse = mse
            best_model = xgb_iter_model
            best_model_name = xgb_name
            
    except ImportError:
        print("XGBoost not installed.")

    # --- 3. Gradient Boosting (Staged) ---
    gb_name = "GradientBoosting"
    gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    with mlflow.start_run(run_name=f"{gb_name}"):
        gb_model.fit(X_train, y_train)
        if wandb.run:
            for i, (val_preds, train_preds) in enumerate(zip(gb_model.staged_predict(X_val), gb_model.staged_predict(X_train))):
                wandb.log({
                    f"{gb_name}_val_mse": mean_squared_error(y_val, val_preds), 
                    f"{gb_name}_val_mae": mean_absolute_error(y_val, val_preds),
                    f"{gb_name}_val_r2": r2_score(y_val, val_preds),
                    
                    f"{gb_name}_train_mse": mean_squared_error(y_train, train_preds), 
                    f"{gb_name}_train_mae": mean_absolute_error(y_train, train_preds),
                    f"{gb_name}_train_r2": r2_score(y_train, train_preds),
                    
                    "iteration": i+1
                })
        
        final_preds = gb_model.predict(X_val)
        mse = mean_squared_error(y_val, final_preds)
        print(f"  {gb_name} - Val MSE: {mse:.6f}")
        if mse < best_mse:
            best_mse = mse
            best_model = gb_model
            best_model_name = gb_name

    # --- 4. SVR (Single Point) ---
    from sklearn.svm import SVR
    svr_name = "SVR"
    svr_model = SVR(kernel='rbf')
    with mlflow.start_run(run_name=f"{svr_name}"):
        svr_model.fit(X_train, y_train)
        preds = svr_model.predict(X_val)
        mse = mean_squared_error(y_val, preds)
        print(f"  {svr_name} - Val MSE: {mse:.6f}")
        mlflow.log_metrics({"val_mse": mse})
        if mse < best_mse:
            best_mse = mse
            best_model = svr_model
            best_model_name = svr_name
            
    # --- 5. ElasticNet (Single Point) ---
    from sklearn.linear_model import ElasticNet
    en_name = "ElasticNet"
    en_model = ElasticNet(alpha=0.1, l1_ratio=0.5)
    with mlflow.start_run(run_name=f"{en_name}"):
        en_model.fit(X_train, y_train)
        preds = en_model.predict(X_val)
        mse = mean_squared_error(y_val, preds)
        print(f"  {en_name} - Val MSE: {mse:.6f}")
        if mse < best_mse:
            best_mse = mse
            best_model = en_model
            best_model_name = en_name

    # --- Linear Regression (Baseline) ---
    lr_name = "LinearRegression"
    lr_model = LinearRegression()
    with mlflow.start_run(run_name=f"{lr_name}"):
        lr_model.fit(X_train, y_train)
        preds = lr_model.predict(X_val)
        mse = mean_squared_error(y_val, preds)
        print(f"  {lr_name} - Val MSE: {mse:.6f}")

    # Register Best Model & Final Test
    if best_model:
        print(f"\n🏆 Best Model selected on Validation set: {best_model_name} (Val MSE: {best_mse:.6f})")
        
        # Evaluated on Test Set
        test_preds = best_model.predict(X_test)
        test_mse = mean_squared_error(y_test, test_preds)
        test_mae = mean_absolute_error(y_test, test_preds)
        test_r2 = r2_score(y_test, test_preds)
        
        print(f"🧪 Final Test Evaluation for {best_model_name}:")
        print(f"   MSE: {test_mse:.6f}")
        print(f"   MAE: {test_mae:.6f}")
        print(f"   R2:  {test_r2:.4f}")

        if wandb.run:
             wandb.log({
                "final_test_mse": test_mse,
                "final_test_mae": test_mae,
                "final_test_r2": test_r2
            })

        with mlflow.start_run(run_name=f"BEST_{best_model_name}") as run:
            mlflow.log_metrics({
                "val_mse": best_mse,
                "test_mse": test_mse,
                "test_mae": test_mae,
                "test_r2": test_r2
            })
            mlflow.sklearn.log_model(
                best_model, 
                "model",
                registered_model_name=REGISTERED_MODEL_NAME
            )
            
    if wandb.run:
        wandb.finish()

if __name__ == "__main__":
    train_and_log()