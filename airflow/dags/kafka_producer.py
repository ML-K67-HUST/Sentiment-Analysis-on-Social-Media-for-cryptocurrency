"""
Simple Kafka Producer - Minimal implementation for article IDs
"""
import json
from kafka import KafkaProducer


def send_article_ids(topic: str, hash_ids: list, kafka_server: str = "kafka:9092"):
    """
    Send article hash IDs to Kafka topic
    
    Args:
        topic: Kafka topic name
        hash_ids: List of article hash IDs
        kafka_server: Kafka bootstrap server
    """
    producer = KafkaProducer(
        bootstrap_servers=[kafka_server],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks=1,  # Relaxed for dev environment
        retries=3,
        max_in_flight_requests_per_connection=1  # Ensure ordering
    )
    
    try:
        message = {"hash_ids": hash_ids}
        future = producer.send(topic, value=message)
        producer.flush()  # Ensure message is sent
        
        # Wait for confirmation
        record_metadata = future.get(timeout=10)
        print(f"✅ Sent {len(hash_ids)} IDs to {topic} "
              f"(partition={record_metadata.partition}, offset={record_metadata.offset})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send to Kafka: {e}")
        return False
        
    finally:
        producer.close()
