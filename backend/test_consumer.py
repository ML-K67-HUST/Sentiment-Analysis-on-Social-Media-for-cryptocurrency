#!/usr/bin/env python3
"""Test consumer startup step by step"""
import sys

print("=" * 80, flush=True)
print("🔧 TEST: Starting consumer test...", flush=True)
print("=" * 80, flush=True)

try:
    print("\n1️⃣  Test: Import json...", flush=True)
    import json
    print("✅ json imported", flush=True)
    
    print("\n2️⃣  Test: Import kafka...", flush=True)
    from kafka import KafkaConsumer
    print("✅ kafka imported", flush=True)
    
    print("\n3️⃣  Test: Import database.mongodb...", flush=True)
    from database.mongodb import MongoManager
    print("✅ MongoDB imported", flush=True)
    
    print("\n4️⃣  Test: Import LLM.sentiment_agent...", flush=True)
    from LLM.sentiment_agent import infer_policy
    print("✅ LLM modules imported", flush=True)
    
    print("\n5️⃣  Test: Initialize MongoDB...", flush=True)
    mongo = MongoManager('blog-data')
    print("✅ MongoDB initialized", flush=True)
    
    print("\n6️⃣  Test: Create Kafka consumer (this may take time)...", flush=True)
    consumer = KafkaConsumer(
        bootstrap_servers=["kafka:9092"],
        group_id="test-group",
        value_deserializer=json.loads,
        auto_offset_reset="earliest",
        consumer_timeout_ms=5000  # 5s timeout
    )
    print("✅ Kafka consumer created", flush=True)
    
    print("\n✅ ALL TESTS PASSED!", flush=True)
    print("=" * 80, flush=True)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)


