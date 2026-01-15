#!/bin/bash
# Helper script to run consumers locally
# Usage: ./scripts/run_consumer.sh [sentiment|nlp|llm]

SERVICE=$1

if [ -z "$SERVICE" ]; then
    echo "Usage: ./scripts/run_consumer.sh [sentiment|nlp|llm]"
    exit 1
fi

# Set PYTHONPATH to include project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

if [ "$SERVICE" == "sentiment" ]; then
    echo "Starting Sentiment Consumer..."
    python backend/consumers/sentiment_consumer.py
elif [ "$SERVICE" == "nlp" ]; then
    echo "Starting NLP Consumer..."
    python backend/consumers/nlp_consumer.py
elif [ "$SERVICE" == "llm" ]; then
    echo "Starting LLM Consumer..."
    python backend/consumers/llm_consumer.py
else
    echo "Unknown consumer: $SERVICE"
    echo "Available: sentiment, nlp, llm"
    exit 1
fi
