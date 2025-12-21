import joblib
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import os

# Create dummy data with 17 features (matching the new model input)
# Shape: (5, 17) to fit the scaler
X_dummy = np.random.rand(10, 17)

# Initialize and fit scaler
scaler = MinMaxScaler()
scaler.fit(X_dummy)

# Save to file
output_path = 'scaler_10min.pkl'
joblib.dump(scaler, output_path)

print(f"✅ Created {output_path} expecting 17 features.")
print(f"Scale: {scaler.scale_}")
print(f"Min: {scaler.min_}")
