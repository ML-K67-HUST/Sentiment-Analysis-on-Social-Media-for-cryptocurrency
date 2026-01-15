#!/usr/bin/env python3
"""
Baseline Models for Price Prediction Comparison
Purpose: Prove that sentiment features add value beyond pure price history

Baselines:
1. Naive: ŷ_t+1 = y_t (price stays constant)
2. Moving Average: ŷ_t+1 = mean(last k windows)
3. ARIMA: Uses AR(p) + I(d) + MA(q) on price only

All baselines use ONLY historical price, NO sentiment features.
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentiman_labeled_data.csv")

def load_data():
    """Load the same dataset used by main Random Forest model"""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"{DATA_PATH} not found. Run data_constructor.py first.")
    
    df = pd.read_csv(DATA_PATH)
    print(f"✅ Loaded {len(df)} samples from {DATA_PATH}")
    
    # Sort by time
    if 'window_start' in df.columns:
        df = df.sort_values('window_start').reset_index(drop=True)
    
    return df

def create_train_test_split(df, train_ratio=0.70, val_ratio=0.15):
    """
    Time-series split matching the main model
    70% train, 15% val, 15% test
    """
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    
    train = df.iloc[:train_end]
    val = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]
    
    print(f"\n📊 Split: Train={len(train)}, Val={len(val)}, Test={len(test)}")
    return train, val, test

def evaluate_predictions(y_true, y_pred, model_name):
    """Calculate metrics"""
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    print(f"\n📈 {model_name} Results:")
    print(f"   MAE: {mae:.6f}")
    print(f"   MSE: {mse:.6f}")
    print(f"   R²:  {r2:.4f}")
    
    return {'model': model_name, 'mae': mae, 'mse': mse, 'r2': r2}

# ========== BASELINE 1: Naive (Persistence) ==========
def naive_baseline(train, val, test, target_col='price_movement_10min'):
    """
    Naive baseline: ŷ_t+1 = y_t
    Assumes price change will be 0 (no movement)
    """
    print("\n" + "="*60)
    print("BASELINE 1: NAIVE (Persistence)")
    print("="*60)
    print("Hypothesis: ŷ_t+1 = y_t (tomorrow = today)")
    
    # For price MOVEMENT, naive prediction is 0
    # (price will not change from current level)
    y_test = test[target_col].values
    y_pred = np.zeros(len(y_test))
    
    return evaluate_predictions(y_test, y_pred, "Naive")

# ========== BASELINE 2: Moving Average ==========
def moving_average_baseline(train, val, test, target_col='price_movement_10min', window_size=6):
    """
    Moving Average: ŷ_t+1 = mean(y_t-k, ..., y_t)
    Uses last k observations
    """
    print("\n" + "="*60)
    print(f"BASELINE 2: MOVING AVERAGE (k={window_size})")
    print("="*60)
    print(f"Hypothesis: ŷ_t+1 = mean of last {window_size} movements")
    
    # Combine train+val for historical context
    historical = pd.concat([train, val])
    all_data = pd.concat([historical, test])
    
    y_test = test[target_col].values
    y_pred = []
    
    test_start_idx = len(historical)
    
    for i in range(test_start_idx, len(all_data)):
        # Get last k values
        window = all_data[target_col].iloc[max(0, i-window_size):i].values
        if len(window) == 0:
            pred = 0
        else:
            pred = np.mean(window)
        y_pred.append(pred)
    
    y_pred = np.array(y_pred)
    
    return evaluate_predictions(y_test, y_pred, "Moving Average")

# ========== BASELINE 3: ARIMA ==========
def arima_baseline(train, val, test, target_col='price_movement_10min'):
    """
    ARIMA: Autoregressive Integrated Moving Average
    Uses only historical price movements (no sentiment)
    """
    print("\n" + "="*60)
    print("BASELINE 3: ARIMA (p=5, d=0, q=0)")
    print("="*60)
    print("Uses: AR(5) - only past 5 price movements")
    
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except ImportError:
        print("⚠️  statsmodels not installed. Skipping ARIMA.")
        print("   Install: pip install statsmodels")
        return {'model': 'ARIMA', 'mae': np.nan, 'mse': np.nan, 'r2': np.nan}
    
    # Train on train+val
    historical = pd.concat([train, val])
    train_series = historical[target_col].values
    
    # Fit ARIMA model
    print("Training ARIMA...")
    try:
        model = ARIMA(train_series, order=(5, 0, 0))  # AR(5)
        fitted = model.fit()
        
        # Forecast test period
        y_test = test[target_col].values
        n_forecast = len(y_test)
        
        # Rolling forecast (more realistic)
        y_pred = []
        history = list(train_series)
        
        for i in range(n_forecast):
            model_temp = ARIMA(history, order=(5, 0, 0))
            fitted_temp = model_temp.fit()
            forecast = fitted_temp.forecast(steps=1)[0]
            y_pred.append(forecast)
            
            # Update history with actual value
            history.append(y_test[i])
        
        y_pred = np.array(y_pred)
        
        return evaluate_predictions(y_test, y_pred, "ARIMA")
        
    except Exception as e:
        print(f"❌ ARIMA failed: {e}")
        return {'model': 'ARIMA', 'mae': np.nan, 'mse': np.nan, 'r2': np.nan}

# ========== Main Execution ==========
def main():
    print("="*60)
    print("🎯 BASELINE MODELS EVALUATION")
    print("="*60)
    print("\nGoal: Prove sentiment features add value")
    print("Method: Compare RF (with sentiment) vs baselines (price only)\n")
    
    # Load data
    df = load_data()
    
    # Check target column
    target_col = 'price_movement_10min'
    if target_col not in df.columns:
        print(f"❌ Target column '{target_col}' not found!")
        print(f"Available columns: {df.columns.tolist()}")
        return
    
    # Split
    train, val, test = create_train_test_split(df)
    
    # Run baselines
    results = []
    
    results.append(naive_baseline(train, val, test, target_col))
    results.append(moving_average_baseline(train, val, test, target_col))
    results.append(arima_baseline(train, val, test, target_col))
    
    # Summary table
    print("\n" + "="*60)
    print("📊 BASELINE COMPARISON SUMMARY")
    print("="*60)
    print(f"{'Model':<20} {'MAE':<12} {'MSE':<12} {'R²':<8}")
    print("-"*60)
    
    for res in results:
        print(f"{res['model']:<20} {res['mae']:<12.6f} {res['mse']:<12.6f} {res['r2']:<8.4f}")
    
    print("\n💡 Interpretation:")
    print("   - R² near 0: Model no better than naive")
    print("   - R² negative: Model worse than naive")
    print("   - If RF (with sentiment) >> baselines → Sentiment has value!")
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv('baseline_results.csv', index=False)
    print(f"\n💾 Results saved to baseline_results.csv")

if __name__ == "__main__":
    main()
