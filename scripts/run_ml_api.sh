#!/bin/bash
# Helper script to run ML API locally
# Usage: ./scripts/run_ml_api.sh

# Set PYTHONPATH to include project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "Starting ML API..."
python -m uvicorn backend.services.ml_api:app --host 0.0.0.0 --port 8002
