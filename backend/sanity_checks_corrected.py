#!/usr/bin/env python3
"""
CORRECTED Sanity Checks - Addressing R² ≠ ρ² Paradox
Root cause: We measured autocorr on return_1 but predicted price_movement_10min
Fix: Measure both on SAME variable (price_movement_10min)
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentiman_with_price.csv")

print("="*70)
print("🔧 CORRECTED SANITY CHECKS")
print("="*70)
print("\nFIXING: R² ≠ ρ² paradox")
print("Issue: Measured autocorr on 'return_1' but predicted 'price_movement_10min'")
print("Fix: Use SAME variable for both\n")

# Load data
df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=['price_movement_10min'])
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
# CHECK 1: CORRECTED AUTOCORRELATION (on TARGET variable)
# ============================================================================

print("="*70)
print("CHECK 1: AUTOCORRELATION OF TARGET (price_movement_10min)")
print("="*70)
print("Computing autocorr on the SAME variable we're trying to predict\n")

target = df['price_movement_10min'].dropna().values

# Lag-1 autocorrelation of TARGET
autocorr_target_1 = np.corrcoef(target[:-1], target[1:])[0, 1]
autocorr_target_2 = np.corrcoef(target[:-2], target[2:])[0, 1]
autocorr_target_3 = np.corrcoef(target[:-3], target[3:])[0, 1]

print(f"Lag-1 autocorrelation (target): {autocorr_target_1:.4f}")
print(f"Lag-2 autocorrelation (target): {autocorr_target_2:.4f}")
print(f"Lag-3 autocorrelation (target): {autocorr_target_3:.4f}")

print(f"\n📊 Expected AR(1) R²: {autocorr_target_1**2:.4f} (= ρ²)")

# ============================================================================
# CHECK 2: CORRECTED AR(1) - Using y[t-1] to predict y[t]
# ============================================================================

print("\n" + "="*70)
print("CHECK 2: CORRECTED AR(1) BASELINE")
print("="*70)
print("Model: price_movement[t] = β₀ + β₁ × price_movement[t-1]\n")

# Create lagged target
df['target_lag1'] = df['price_movement_10min'].shift(1)

# Remove NaN
df_ar = df.dropna(subset=['price_movement_10min', 'target_lag1'])

# Re-split after lag creation
n_ar = len(df_ar)
train_end_ar = int(n_ar * 0.70)
val_end_ar = int(n_ar * 0.85)

train_ar = df_ar.iloc[:train_end_ar]
test_ar = df_ar.iloc[val_end_ar:]

# Prepare AR(1) data
X_train_ar1 = train_ar[['target_lag1']].values
y_train_ar1 = train_ar['price_movement_10min'].values

X_test_ar1 = test_ar[['target_lag1']].values
y_test_ar1 = test_ar['price_movement_10min'].values

print(f"AR(1) Train samples: {len(X_train_ar1)}")
print(f"AR(1) Test samples: {len(X_test_ar1)}")

# Fit AR(1)
ar1_model = LinearRegression()
ar1_model.fit(X_train_ar1, y_train_ar1)

# Predict
y_pred_ar1 = ar1_model.predict(X_test_ar1)

# Evaluate
r2_ar1 = r2_score(y_test_ar1, y_pred_ar1)
mae_ar1 = mean_absolute_error(y_test_ar1, y_pred_ar1)
mse_ar1 = mean_squared_error(y_test_ar1, y_pred_ar1)

print(f"\nAR(1) Test Results:")
print(f"   R²:  {r2_ar1:.4f}")
print(f"   MAE: {mae_ar1:.6f}")
print(f"   MSE: {mse_ar1:.6f}")
print(f"   β₁:  {ar1_model.coef_[0]:.4f}")
print(f"   β₀:  {ar1_model.intercept_:.6f}")

# Verify R² ≈ ρ²
expected_r2 = autocorr_target_1 ** 2
r2_error = abs(r2_ar1 - expected_r2)

print(f"\n📐 Mathematical Verification:")
print(f"   Expected R² (ρ²):   {expected_r2:.4f}")
print(f"   Actual R² (AR(1)):  {r2_ar1:.4f}")
print(f"   Error:              {r2_error:.4f}")

if r2_error < 0.01:
    print(f"\n✅ PASS: R² ≈ ρ² (error < 0.01)")
    print("   → Mathematical consistency verified")
else:
    print(f"\n⚠️  WARNING: R² ≠ ρ² (error = {r2_error:.4f})")
    print("   → Check for numerical issues or data problems")

# Interpretation
if r2_ar1 > 0.1:
    print(f"\n🔍 INTERPRETATION:")
    print(f"   AR(1) achieves R² = {r2_ar1:.4f} (non-trivial)")
    print(f"   → Target has {r2_ar1*100:.1f}% autocorrelation-based predictability")
    print(f"   → Technical baseline SHOULD perform better than this")
    print(f"   → Our RF baseline (R²=-0.02) underperforming AR(1) is SUSPICIOUS")
elif r2_ar1 > 0:
    print(f"\n🔍 INTERPRETATION:")
    print(f"   AR(1) achieves R² = {r2_ar1:.4f} (weak but positive)")
    print(f"   → Minimal autocorrelation-based predictability")
    print(f"   → Technical baseline R²=-0.02 is close to this")
else:
    print(f"\n🔍 INTERPRETATION:")
    print(f"   AR(1) achieves R² = {r2_ar1:.4f} (negative)")
    print(f"   → No autocorrelation-based predictability")
    print(f"   → Validates that technical baseline is legitimately weak")

# ============================================================================
# CHECK 3: Compare with Technical Baseline
# ============================================================================

print("\n" + "="*70)
print("CHECK 3: AR(1) vs RF Technical Baseline")
print("="*70)

print(f"\n📊 Comparison:")
print(f"   AR(1) (simple):         R² = {r2_ar1:+.4f}")
print(f"   RF Technical (complex): R² = -0.02")

if r2_ar1 > 0.05:
    print(f"\n🚨 CONCERN:")
    print(f"   Simple AR(1) outperforms complex RF baseline ({r2_ar1:.4f} > -0.02)")
    print(f"   Possible explanations:")
    print(f"     1. RF regularization too strong (depth=5, noise injection)")
    print(f"     2. RF fails to capture simple linear pattern")
    print(f"     3. Technical features (RSI, MACD) add noise, not signal")
    
    print(f"\n💡 RECOMMENDATION:")
    print(f"   Use AR(1) R² = {r2_ar1:.4f} as the honest technical baseline")
    print(f"   Full model R² = 0.83")
    print(f"   Improvement: ΔR² = {0.83 - r2_ar1:.4f}")
elif r2_ar1 > -0.02:
    print(f"\n✅ CONSISTENT:")
    print(f"   AR(1) and RF baseline perform similarly ({r2_ar1:.4f} vs -0.02)")
    print(f"   Both confirm weak predictability from price history alone")
else:
    print(f"\n⚠️  AR(1) worse than RF baseline")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("📊 CORRECTED DIAGNOSTIC SUMMARY")
print("="*70)

print(f"\n1. Target Autocorrelation (ρ):      {autocorr_target_1:+.4f}")
print(f"2. AR(1) R² (actual):               {r2_ar1:+.4f}")
print(f"3. Expected R² (ρ²):                {expected_r2:+.4f}")
print(f"4. Mathematical consistency:        {'✅ PASS' if r2_error < 0.01 else '❌ FAIL'}")

if r2_ar1 > 0.05:
    print(f"\n⚠️  IMPLICATION:")
    print(f"   AR(1) R² = {r2_ar1:.4f} suggests technical baseline COULD be stronger")
    print(f"   Consider using AR(1) R² as the honest baseline for comparison")
else:
    print(f"\n✅ VALIDATION:")
    print(f"   Both AR(1) and RF baselines confirm weak predictability")

print(f"\n💾 Analysis complete.")
