from kafka import KafkaProducer
from json import dumps, loads
import time
from constants.config import KAFKA_HOST, KAFKA_PORT, KAFKA_USERNAME, KAFKA_PASSWORD


class Kafka:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return

        # self.bootstrap_servers = bootstrap_servers
        # self.topic = topic
        self.producer = KafkaProducer(
            # bootstrap_servers=[f"{KAFKA_HOST}:{KAFKA_PORT}"],
            bootstrap_servers=["127.0.0.1"],
            value_serializer=lambda x: dumps(x).encode("utf-8"),
            # security_protocol="SASL_PLAINTEXT",
            # sasl_mechanism="SCRAM-SHA-256",
            # sasl_plain_username=KAFKA_USERNAME,
            # sasl_plain_password=KAFKA_PASSWORD,
        )

    def producer_send(self, topic, message):
        try:
            self.producer.send(topic, message)
            self.producer.flush()
            print("SEND DONE TO: ", topic)

        except Exception as e:
            print(e)
