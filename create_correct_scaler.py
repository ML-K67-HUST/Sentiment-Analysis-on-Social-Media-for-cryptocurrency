import joblib
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import os

X_dummy = np.random.rand(10, 17)

scaler = MinMaxScaler()
scaler.fit(X_dummy)
output_path = 'scaler_10min.pkl'
joblib.dump(scaler, output_path)

print(f"✅ Created {output_path} expecting 17 features.")
print(f"Scale: {scaler.scale_}")
print(f"Min: {scaler.min_}")
