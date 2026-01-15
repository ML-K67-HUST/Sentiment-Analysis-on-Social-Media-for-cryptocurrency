import json
from datetime import datetime
from time import sleep
from random import choice
import sys
import os

# Allow running from producer directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka import KafkaProducer
from backend.config import config

kafka_server = [config.KAFKA_BOOTSTRAP_SERVERS]
topic = config.KAFKA_TOPIC

producer = KafkaProducer(
    bootstrap_servers=kafka_server,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

random_values = [1, 2, 3, 4, 5, 6, 7]

while True:
    random_value = choice(random_values)
    data = {
        "test_data": {
            "random_value": random_value
        },
        "timestamp": str(datetime.now()),
        "value_status": "High" if random_value > 5 else "Low"
    }
    print(data)
    producer.send(topic, data)
    producer.flush()
    sleep(3)