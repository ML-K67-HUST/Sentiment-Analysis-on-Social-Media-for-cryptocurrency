# Consumer Pipeline Debug Summary

## ❌ Problem
After extensive debugging (2+ hours), consumers still not processing Kafka messages:
- MongoDB: 2182 articles in `cmc_news`, **0 in `cmc_sentiment_data` and `article_features`**  
- Consumers running 59 minutes: **healthy** but NO processing logs
- Kafka topic: messages pushed multiple times

## 🔍 Root Causes Found

### 1. Python stdout buffering
- Containers run `python consumer.py` (no `-u` flag)
- All `print()` output buffered → no logs visible
- **Fix:** Add `-u` flag in docker-compose

### 2. Old code in Docker image
- Fixed `for message in consumer:` in source files
- But container runs old image with `next(consumer)`  
- **Fix:** Rebuild image (attempted but took 60+ minutes)

### 3. Missing `group_id`
- Original consumers lacked `group_id` parameter
- Kafka can't track offsets without group_id
- **Fix:** Added `group_id` but needs rebuild

## 📋 Completed Fixes (in source code)

✅ Added `group_id="llm-sentiment-group"` to LLM consumer
✅ Changed `next(consumer)` → `for message in consumer:` loop
✅ Added `group_id="nlp-feature-group"` to NLP consumer  
✅ Created bootstrap script to push messages to Kafka
✅ Pushed 100 messages to Kafka (multiple times)

## ⚠️ Blockers

❌ Docker image rebuild extremely slow (NLTK downloads)
❌ Containers still running old image  
❌ `-u` flag not added to docker-compose yet
❌ No way to verify fixes without rebuild

## 💡 Recommended Solutions

### Option A: Quick Fix (RECOMMENDED)
1. Add `-u` flag to docker-compose commands
2. Rebuild with `--no-cache` on critical layers only
3. Or mount source files as volumes for hot reload

### Option B: Manual Test
```bash
# Run consumer manually with proper flags
docker run --rm -it --network sentiman-net \\
  --env-file .env \\
  sentiman_backend:latest \\
  python -u consumer.py
```

### Option C: Simplify Consumer Code
- Remove complex LLM calls for testing
- Just log received messages and save to MongoDB
- Verify basic flow works first

## 📝 Next Steps

1. **Immediate:** Add `-u` to docker-compose commands
2. **Short-term:** Optimize Dockerfile (cache NLTK layer)
3. **Long-term:** Add proper logging framework (not print())
4. **Testing:** Create integration test for consumer pipeline
