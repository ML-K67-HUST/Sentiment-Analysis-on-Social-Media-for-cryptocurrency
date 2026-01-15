import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from airflow.dags.common.processor import get_random_headers, fetch

print("Testing Random Headers:")
for i in range(3):
    print(f"[{i+1}] {get_random_headers()['User-Agent']}")

print("\nTesting Fetch Function (Dry Run - no network needed if mocked, but here we test import):")
try:
    # Just checking if function exists and imports work
    headers = get_random_headers()
    print("✅ Import and Header Generation successful")
except Exception as e:
    print(f"❌ Error: {e}")
