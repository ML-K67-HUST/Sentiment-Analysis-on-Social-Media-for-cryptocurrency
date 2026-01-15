#!/usr/bin/env python3
"""
Ablation Study: Quantifying the Impact of Sentiment Features
Compares Random Forest performance with and without sentiment features

Approach:
1. Technical-Only Baseline: Uses only article count (no sentiment)
2. Full Model: Uses all sentiment features
3. Same dataset, same split, same test set → Fair comparison
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

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentiman_labeled_data.csv")

# Feature definitions
TECHNICAL_ONLY = ['num_articles']

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

FULL_FEATURES = TECHNICAL_ONLY + SENTIMENT_FEATURES

def load_and_split():
    """Load data and create time-series split"""
    df = pd.read_csv(DATA_PATH)
    print(f"✅ Loaded {len(df)} samples")
    
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
    
    print(f"📊 Split: Train={len(train)}, Val={len(val)}, Test={len(test)}")
    return train, val, test

def train_and_evaluate(train, val, test, features, model_name, target_col='price_movement_10min'):
    """Train RF and evaluate"""
    print(f"\n{'='*60}")
    print(f"Training: {model_name}")
    print(f"Features ({len(features)}): {features[:3]}{'...' if len(features) > 3 else ''}")
    print(f"{'='*60}")
    
    # Check if features exist
    available = [f for f in features if f in train.columns]
    missing = set(features) - set(available)
    
    if missing:
        print(f"⚠️  Missing features: {missing}")
        print(f"   Using only: {available}")
        features = available
    
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
    
    # Train Random Forest
    print("Training Random Forest...")
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    
    # Evaluate on test set
    y_pred = rf.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n📈 Test Results:")
    print(f"   MAE: {mae:.6f}")
    print(f"   MSE: {mse:.6f}")
    print(f"   R²:  {r2:.4f}")
    
    # Feature importance (top 5)
    if len(features) > 1:
        importances = rf.feature_importances_
        indices = np.argsort(importances)[::-1][:5]
        print(f"\n🔑 Top 5 Features:")
        for i, idx in enumerate(indices):
            print(f"   {i+1}. {features[idx]}: {importances[idx]:.4f}")
    
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
    print("🔬 ABLATION STUDY: Sentiment Feature Impact")
    print("="*60)
    print("\nGoal: Isolate the contribution of sentiment features")
    print("Method: Compare same RF model with/without sentiment\n")
    
    # Load data
    train, val, test = load_and_split()
    
    # Check target
    target_col = 'price_movement_10min'
    if target_col not in train.columns:
        print(f"❌ Target '{target_col}' not found!")
        return
    
    # Experiment 1: Technical-Only
    result_tech = train_and_evaluate(
        train, val, test,
        TECHNICAL_ONLY,
        "Technical-Only Baseline"
    )
    
    # Experiment 2: Full Features
    result_full = train_and_evaluate(
        train, val, test,
        FULL_FEATURES,
        "Full Model (Technical + Sentiment)"
    )
    
    # Comparison
    print("\n" + "="*60)
    print("📊 ABLATION STUDY RESULTS")
    print("="*60)
    print(f"{'Model':<35} {'Features':<10} {'MAE':<12} {'MSE':<12} {'R²':<8}")
    print("-"*60)
    
    if result_tech:
        print(f"{result_tech['model_name']:<35} {result_tech['n_features']:<10} "
              f"{result_tech['mae']:<12.6f} {result_tech['mse']:<12.6f} {result_tech['r2']:<8.4f}")
    
    if result_full:
        print(f"{result_full['model_name']:<35} {result_full['n_features']:<10} "
              f"{result_full['mae']:<12.6f} {result_full['mse']:<12.6f} {result_full['r2']:<8.4f}")
    
    # Calculate improvement
    if result_tech and result_full:
        delta_r2 = result_full['r2'] - result_tech['r2']
        delta_mae = result_tech['mae'] - result_full['mae']  # Lower is better
        
        print("\n" + "="*60)
        print("💡 SENTIMENT FEATURE CONTRIBUTION")
        print("="*60)
        print(f"ΔR²:  {delta_r2:+.4f} ({'improvement' if delta_r2 > 0 else 'degradation'})")
        print(f"ΔMAE: {delta_mae:+.6f} (negative = better)")
        
        if delta_r2 > 0.1:
            print(f"\n✅ CONCLUSION: Sentiment features provide SIGNIFICANT value")
            print(f"   Adding {len(SENTIMENT_FEATURES)} sentiment features improved R² by {delta_r2:.2%}")
        elif delta_r2 > 0:
            print(f"\n⚠️  CONCLUSION: Sentiment features provide modest improvement")
        else:
            print(f"\n❌ CONCLUSION: Sentiment features did not improve performance")
    
    # Save results
    results_df = pd.DataFrame([result_tech, result_full])
    results_df.to_csv('ablation_study_results.csv', index=False)
    print(f"\n💾 Results saved to ablation_study_results.csv")

if __name__ == "__main__":
    main()
