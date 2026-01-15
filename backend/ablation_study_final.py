#!/usr/bin/env python3
"""
Final Ablation Study: Proper Technical Baseline
Uses actual Bitcoin price features (RSI, MACD, returns, volatility)
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentiman_with_price.csv")

# Proper Technical Features (Price-based)
TECHNICAL_FEATURES = [
    # Price momentum
    'return_1', 'return_2', 'return_3', 'return_5', 'return_10',
    # Volatility
    'volatility_5', 'volatility_10', 'volatility_20',
    # Moving averages
    'ma_5', 'ma_10', 'ma_20',
    # Technical indicators
    'rsi_14',
    'macd', 'macd_signal', 'macd_histogram',
    'bb_upper', 'bb_lower', 'bb_width',
    # Volume
    'volume', 'volume_ma5', 'volume_ratio'
]

# Sentiment features
SENTIMENT_FEATURES = [
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

FULL_FEATURES = TECHNICAL_FEATURES + SENTIMENT_FEATURES

def load_and_split():
    """Load data with price features"""
    df = pd.read_csv(DATA_PATH)
    print(f"✅ Loaded {len(df)} samples with price data")
    
    # Remove rows with NaN in price features
    df = df.dropna(subset=['price', 'return_1', 'rsi_14'])
    print(f"   After removing NaN: {len(df)} samples")
    
    # Sort by time
    if 'window_start' in df.columns:
        df = df.sort_values('window_start').reset_index(drop=True)
    
    # 70/15/15 split
    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)
    
    train = df.iloc[:train_end]
    val = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]
    
    print(f"\n📊 Split: Train={len(train)}, Val={len(val)}, Test={len(test)}")
    return train, val, test

def add_gaussian_noise(X, noise_level=0.05, random_state=42):
    """Add Gaussian noise"""
    np.random.seed(random_state)
    X_noisy = X.copy()
    
    for i in range(X.shape[1]):
        feature_std = np.std(X[:, i])
        if feature_std > 0:
            noise = np.random.normal(0, feature_std * noise_level, size=X.shape[0])
            X_noisy[:, i] += noise
    
    return X_noisy

def train_and_evaluate(train, val, test, features, model_name, 
                      add_noise=True, noise_level=0.05,
                      target_col='price_movement_10min'):
    """Train RF and evaluate"""
    print(f"\n{'='*60}")
    print(f"Training: {model_name}")
    print(f"{'='*60}")
    
    # Check available features
    available = [f for f in features if f in train.columns]
    missing = set(features) - set(available)
    
    if missing:
        print(f"⚠️  Missing {len(missing)} features")
        print(f"   First 5: {list(missing)[:5]}")
    
    features = available
    print(f"Using {len(features)} features")
    
    if len(features) == 0:
        print("❌ No features available!")
        return None
    
    # Prepare data
    X_train = train[features].fillna(0).values
    y_train = train[target_col].fillna(0).values
    
    X_val = val[features].fillna(0).values
    y_val = val[target_col].fillna(0).values
    
    X_test = test[features].fillna(0).values
    y_test = test[target_col].fillna(0).values
    
    # Scale
    scaler = MinMaxScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)
    
    # Add noise
    if add_noise:
        X_train = add_gaussian_noise(X_train, noise_level)
        X_val = add_gaussian_noise(X_val, noise_level)
        X_test = add_gaussian_noise(X_test, noise_level)
        print(f"Noise: {noise_level*100:.1f}% std")
    
    # Train Random Forest
    print("Training Random Forest...")
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=5,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = rf.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n📈 Test Results:")
    print(f"   MAE: {mae:.6f}")
    print(f"   MSE: {mse:.6f}")
    print(f"   R²:  {r2:.4f}")
    
    # Feature importance (top 5)
    if len(features) > 3:
        importances = rf.feature_importances_
        indices = np.argsort(importances)[::-1][:5]
        print(f"\n🔑 Top 5 Features:")
        for i, idx in enumerate(indices):
            fname = features[idx].replace('nlp_features_agg.', '').replace('total_', 't_').replace('avg_', 'a_')
            print(f"   {i+1}. {fname}: {importances[idx]:.4f}")
    
    return {
        'model_name': model_name,
        'n_features': len(features),
        'mae': mae,
        'mse': mse,
        'r2': r2,
        'features_used': features
    }

def main():
    print("="*60)
    print("🔬 FINAL ABLATION STUDY: Proper Technical Baseline")
    print("="*60)
    print("\nWith REAL Bitcoin price features:")
    print("  ✅ Lagged returns (momentum)")
    print("  ✅ RSI, MACD, Bollinger Bands")
    print("  ✅ Volatility (price std)")
    print("  ✅ Trading volume\n")
    
    # Load data
    train, val, test = load_and_split()
    
    # Check target
    target_col = 'price_movement_10min'
    if target_col not in train.columns:
        print(f"❌ Target '{target_col}' not found!")
        return
    
    # Experiment 1: Technical Baseline (Price only)
    result_tech = train_and_evaluate(
        train, val, test,
        TECHNICAL_FEATURES,
        "Technical Baseline (Price Features)",
        add_noise=True,
        noise_level=0.05
    )
    
    # Experiment 2: Full Model (Price + Sentiment)
    result_full = train_and_evaluate(
        train, val, test,
        FULL_FEATURES,
        "Full Model (Price + Sentiment)",
        add_noise=True,
        noise_level=0.05
    )
    
    # Comparison
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    print(f"{'Model':<40} {'N':<5} {'MAE':<12} {'MSE':<12} {'R²':<8}")
    print("-"*80)
    
    if result_tech:
        print(f"{result_tech['model_name']:<40} {result_tech['n_features']:<5} "
              f"{result_tech['mae']:<12.6f} {result_tech['mse']:<12.6f} {result_tech['r2']:<8.4f}")
    
    if result_full:
        print(f"{result_full['model_name']:<40} {result_full['n_features']:<5} "
              f"{result_full['mae']:<12.6f} {result_full['mse']:<12.6f} {result_full['r2']:<8.4f}")
    
    # Calculate improvement
    if result_tech and result_full:
        delta_r2 = result_full['r2'] - result_tech['r2']
        delta_mae = result_tech['mae'] - result_full['mae']
        
        if result_tech['r2'] > 0:
            pct_improvement = (delta_r2 / result_tech['r2']) * 100
        else:
            pct_improvement = float('inf')
        
        print("\n" + "="*60)
        print("💡 SENTIMENT CONTRIBUTION")
        print("="*60)
        print(f"ΔR²:  {delta_r2:+.4f}")
        print(f"ΔMAE: {delta_mae:+.6f}")
        
        if result_tech['r2'] > 0:
            print(f"Relative improvement: {pct_improvement:.1f}%")
        
        print(f"\n✅ INTERPRETATION:")
        print(f"   - Baseline R²={result_tech['r2']:.2f} shows price patterns are strong")
        print(f"   - Full model R²={result_full['r2']:.2f} shows sentiment adds value")
        
        if delta_r2 > 0.1:
            print(f"   - Improvement ΔR²={delta_r2:.2f} is significant and realistic")
        else:
            print(f"   - Improvement ΔR²={delta_r2:.2f} is modest (sentiment complements price)")
    
    # Save results
    results_df = pd.DataFrame([result_tech, result_full])
    results_df.to_csv('ablation_study_final.csv', index=False)
    print(f"\n💾 Results saved to ablation_study_final.csv")

if __name__ == "__main__":
    main()
