import json
from kafka import KafkaConsumer, KafkaProducer
from database.mongodb import MongoClient

mongo_client = MongoClient('blog-data')

kafka_server = ["127.0.0.1"]

topic = "coinmarketcap-news"

consumer = KafkaConsumer(
    bootstrap_servers=kafka_server,
    value_deserializer=json.loads,
    auto_offset_reset="latest",
)

consumer.subscribe(topic)

while True:
    data = next(consumer)
    print(data)
    print(data.value)

