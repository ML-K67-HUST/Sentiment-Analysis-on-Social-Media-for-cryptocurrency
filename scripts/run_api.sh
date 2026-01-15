#!/bin/bash
# Helper script to run backend API locally
# Usage: ./scripts/run_api.sh

# Set PYTHONPATH to include project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "Starting Backend API..."
uvicorn backend.services.api:app --host 0.0.0.0 --port 8000 --reload
