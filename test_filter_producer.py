from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

# BTC: 69467bc6f8f384051bd6b5f3
# NEAR: 694637ce03bea125989c63ef
msg = {"hash_ids": ["69467bc6f8f384051bd6b5f3", "694637ce03bea125989c63ef"]}

producer.send('coinmarketcap-news', value=msg)
producer.flush()
print("Sent test message with Mixed BTC and NEAR articles")
