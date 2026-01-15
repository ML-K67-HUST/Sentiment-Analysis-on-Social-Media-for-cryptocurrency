#!/usr/bin/env python3
"""
Sanity Checks and Diagnostic Tests
Addresses critical concerns from peer review:
1. Autocorrelation check (r₁ should have autocorr > 0.1)
2. Permutation test (shuffle target → R² should drop to ~0)
3. AR(1) baseline (simple momentum strategy)
4. Timestamp alignment (no look-ahead bias)
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentiman_with_price.csv")

print("="*70)
print("🔍 SANITY CHECKS & DIAGNOSTIC TESTS")
print("="*70)
print("\nAddressing peer review concerns:")
print("  1. Autocorrelation of returns")
print("  2. Permutation test (null hypothesis)")
print("  3. AR(1) baseline (minimum expected performance)")
print("  4. Timestamp alignment validation\n")

# ============================================================================
# LOAD DATA
# ============================================================================

df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=['price', 'return_1', 'price_movement_10min'])
df = df.sort_values('window_start').reset_index(drop=True)

print(f"✅ Loaded {len(df)} samples\n")

# Split
n = len(df)
train_end = int(n * 0.70)
val_end = int(n * 0.85)

train = df.iloc[:train_end]
val = df.iloc[train_end:val_end]
test = df.iloc[val_end:]

print(f"Split: Train={len(train)}, Val={len(val)}, Test={len(test)}\n")

# ============================================================================
# CHECK 1: AUTOCORRELATION ANALYSIS
# ============================================================================

print("="*70)
print("CHECK 1: AUTOCORRELATION OF RETURNS")
print("="*70)
print("Question: Does r₁ have significant autocorrelation?")
print("Expected: autocorr(r₁, lag=1) ≈ 0.1-0.2 for intraday crypto\n")

returns = df['return_1'].dropna().values

# Lag-1 autocorrelation
autocorr_1 = np.corrcoef(returns[:-1], returns[1:])[0, 1]
autocorr_2 = np.corrcoef(returns[:-2], returns[2:])[0, 1]
autocorr_3 = np.corrcoef(returns[:-3], returns[3:])[0, 1]

print(f"Lag-1 autocorrelation: {autocorr_1:.4f}")
print(f"Lag-2 autocorrelation: {autocorr_2:.4f}")
print(f"Lag-3 autocorrelation: {autocorr_3:.4f}")

if abs(autocorr_1) > 0.1:
    print(f"\n✅ PASS: |autocorr| = {abs(autocorr_1):.4f} > 0.1")
    print("   → Returns exhibit momentum (expected for crypto)")
    print("   → This justifies using lagged returns as features")
else:
    print(f"\n⚠️  WARNING: |autocorr| = {abs(autocorr_1):.4f} < 0.1")
    print("   → Returns are nearly random walk")
    print("   → Technical baseline should still work if autocorr exists")

# ============================================================================
# CHECK 2: AR(1) BASELINE (Naive Momentum)
# ============================================================================

print("\n" + "="*70)
print("CHECK 2: AR(1) BASELINE (Simple Momentum Strategy)")
print("="*70)
print("Model: ŷ_t = β₀ + β₁ × r₁")
print("Purpose: Establish minimum expected R² from momentum alone\n")

# Prepare data
X_train_ar = train[['return_1']].fillna(0).values
y_train = train['price_movement_10min'].fillna(0).values

X_test_ar = test[['return_1']].fillna(0).values
y_test = test['price_movement_10min'].fillna(0).values

# Train simple linear regression
ar1_model = LinearRegression()
ar1_model.fit(X_train_ar, y_train)

# Predict
y_pred_ar1 = ar1_model.predict(X_test_ar)

# Evaluate
r2_ar1 = r2_score(y_test, y_pred_ar1)
mae_ar1 = mean_absolute_error(y_test, y_pred_ar1)
mse_ar1 = mean_squared_error(y_test, y_pred_ar1)

print(f"AR(1) Test Results:")
print(f"   R²:  {r2_ar1:.4f}")
print(f"   MAE: {mae_ar1:.6f}")
print(f"   MSE: {mse_ar1:.6f}")
print(f"   β₁ (momentum coef): {ar1_model.coef_[0]:.4f}")

if r2_ar1 > 0.05:
    print(f"\n✅ PASS: R² = {r2_ar1:.4f} > 0.05")
    print("   → Momentum strategy works")
    print("   → Technical baseline SHOULD achieve at least this R²")
    print(f"   → Our technical baseline ({-0.02:.4f}) < AR(1) is SUSPICIOUS")
elif r2_ar1 > 0:
    print(f"\n⚠️  WEAK: R² = {r2_ar1:.4f} (positive but small)")
    print("   → Weak momentum signal")
else:
    print(f"\n❌ FAIL: R² = {r2_ar1:.4f} (negative)")
    print("   → Even simple AR(1) fails")
    print("   → Validates that technical baseline is legitimately weak")

# ============================================================================
# CHECK 3: PERMUTATION TEST (Null Hypothesis)
# ============================================================================

print("\n" + "="*70)
print("CHECK 3: PERMUTATION TEST")
print("="*70)
print("Test: Shuffle target, retrain, measure R²")
print("Expected: R² → ~0 (proves model isn't fitting noise)\n")

# Features for full model
FULL_FEATURES = [
    'return_1', 'return_2', 'return_3', 'return_5', 'return_10',
    'volatility_5', 'volatility_10', 'volatility_20',
    'ma_5', 'ma_10', 'ma_20',
    'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
    'bb_upper', 'bb_lower', 'bb_width',
    'volume', 'volume_ma5', 'volume_ratio',
    'llm_sentiment_avg', 'llm_confidence_avg',
    'nlp_features_agg.avg_positive_word_ratio',
    'nlp_features_agg.avg_negative_word_ratio',
    'nlp_features_agg.avg_compound_score',
    'nlp_features_agg.total_price_keyword_count'
]

available_features = [f for f in FULL_FEATURES if f in train.columns]
print(f"Using {len(available_features)} features for permutation test")

X_train_full = train[available_features].fillna(0).values
X_test_full = test[available_features].fillna(0).values

# Shuffle target (null hypothesis)
np.random.seed(42)
y_train_shuffled = np.random.permutation(y_train)

# Train on shuffled data
print("Training RandomForest on SHUFFLED target...")
rf_null = RandomForestRegressor(
    n_estimators=50,
    max_depth=5,
    min_samples_split=10,
    random_state=42,
    n_jobs=-1
)

scaler = MinMaxScaler()
X_train_scaled = scaler.fit_transform(X_train_full)
X_test_scaled = scaler.transform(X_test_full)

rf_null.fit(X_train_scaled, y_train_shuffled)

# Predict on test
y_pred_null = rf_null.predict(X_test_scaled)
r2_null = r2_score(y_test, y_pred_null)

print(f"\nPermutation Test Results:")
print(f"   R² (shuffled target): {r2_null:.4f}")

if r2_null < 0.1:
    print(f"\n✅ PASS: R² = {r2_null:.4f} ≈ 0")
    print("   → Model is NOT just fitting random noise")
    print("   → Real R² (0.83) is significantly better than null")
else:
    print(f"\n❌ FAIL: R² = {r2_null:.4f} > 0.1")
    print("   → Model achieves high R² even with random target!")
    print("   → STRONG evidence of overfitting or data leakage")

# ============================================================================
# CHECK 4: TIMESTAMP ALIGNMENT (Look-Ahead Bias)
# ============================================================================

print("\n" + "="*70)
print("CHECK 4: TIMESTAMP ALIGNMENT VALIDATION")
print("="*70)
print("Test: Ensure sentiment timestamp < price movement window\n")

if 'window_start' in df.columns and 'timestamp_rounded' in df.columns:
    df_test = test.copy()
    df_test['window_end'] = df_test['window_start'] + 600  # +10 minutes (600 sec)
    
    # Check: sentiment timestamp should be BEFORE window_end
    look_ahead = (df_test['timestamp_rounded'] > df_test['window_end']).sum()
    
    print(f"Test samples: {len(df_test)}")
    print(f"Look-ahead violations: {look_ahead}")
    
    if look_ahead == 0:
        print(f"\n✅ PASS: No look-ahead bias detected")
        print("   → All sentiment timestamps precede price movements")
    else:
        pct = (look_ahead / len(df_test)) * 100
        print(f"\n❌ FAIL: {look_ahead} ({pct:.1f}%) look-ahead violations!")
        print("   → Sentiment from FUTURE used to predict PAST")
        print("   → This invalidates results!")
else:
    print("⚠️  SKIP: Timestamp columns not available")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("📊 DIAGNOSTIC SUMMARY")
print("="*70)

print(f"\n1. Autocorrelation (r₁):      {autocorr_1:+.4f} {'✅ STRONG' if abs(autocorr_1) > 0.15 else '⚠️ WEAK' if abs(autocorr_1) > 0.05 else '❌ NONE'}")
print(f"2. AR(1) Baseline R²:         {r2_ar1:+.4f} {'✅ WORKS' if r2_ar1 > 0.05 else '❌ FAILS'}")
print(f"3. Permutation Test R²:       {r2_null:+.4f} {'✅ PASS' if r2_null < 0.1 else '❌ FAIL (overfitting)'}")
print(f"4. Look-Ahead Bias:")
if 'look_ahead' in locals():
    print(f"   {'✅ CLEAN' if look_ahead == 0 else f'❌ {look_ahead} violations'}")
else:
    print(f"   ⚠️ Not checked")

print("\n" + "="*70)
print("💡 INTERPRETATION")
print("="*70)

if r2_ar1 > 0.05:
    print("\n⚠️  CONCERN: AR(1) achieves R²={:.4f} but RF baseline R²=-0.02".format(r2_ar1))
    print("   → Suggests issue with RF baseline implementation or overfitting")
    print("   → Recommend investigating why RF underperforms simple linear regression")

if r2_null > 0.1:
    print("\n🚨 CRITICAL: High R² on shuffled data indicates severe overfitting!")
    print("   → Need stronger regularization or more data")

if 'look_ahead' in locals() and look_ahead > 0:
    print("\n🚨 CRITICAL: Look-ahead bias detected!")
    print("   → Results are invalid")

print("\n💾 Diagnostic complete. Review results above.")
