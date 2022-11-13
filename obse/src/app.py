import logging
import os
import sys
import time

from datetime import datetime, timezone

from common import pollRabbitmqReadiness, initRabbitmqConnection

import pika
import requests


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Read configuration from environment variables
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS')
EXCHANGE = os.environ.get('EXCHANGE')
ROUTING_KEY_1 = os.environ.get('ROUTING_KEY_1')
ROUTING_KEY_2 = os.environ.get('ROUTING_KEY_2')
QUEUE_1 = os.environ.get('QUEUE_1')
QUEUE_2 = os.environ.get('QUEUE_2')
FILE = os.environ.get('FILE')


class Counter:
    def __init__(self) -> None:
        self.number = 1

def main():
    # wait until RabbitMQ service is ready, init connection
    pollRabbitmqReadiness(host=RABBITMQ_HOST)
    conn = initRabbitmqConnection(RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS)
    
    # flush file
    with open(file=FILE, mode="w") as f:
        logging.info(f"Flushing {FILE}")
        f.close()
    counter = Counter()

    # Setup messaging
    channel = conn.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic")
    channel.queue_declare(queue=QUEUE_1, exclusive=True)
    channel.queue_declare(queue=QUEUE_2, exclusive=True)
    channel.queue_bind(queue=QUEUE_1, exchange=EXCHANGE, routing_key=ROUTING_KEY_1)
    channel.queue_bind(queue=QUEUE_2, exchange=EXCHANGE, routing_key=ROUTING_KEY_2)
    channel.basic_consume(queue=QUEUE_1, auto_ack=True, on_message_callback=generateCallback(f"{EXCHANGE}.{ROUTING_KEY_1}", counter, filename=FILE))
    channel.basic_consume(queue=QUEUE_2, auto_ack=True, on_message_callback=generateCallback(f"{EXCHANGE}.{ROUTING_KEY_2}", counter, filename=FILE))
    channel.start_consuming()


def generateCallback(topic: str, counter: Counter, filename: str):
    """Inject extra arguments to callback with currying"""
    def callback(channel: pika.channel.Channel, method: pika.spec.Basic.Deliver,
                properties: pika.spec.BasicProperties, body: bytes):
            logging.info(f"Received message from {topic}")
            bodyAsString = body.decode()
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S:%fZ")
            msg = f"{timestamp} {counter.number} {bodyAsString} to {topic}\n"
            with open(file=filename, mode="a", encoding="utf-8") as file:
                file.write(msg)
                file.close()
            counter.number += 1
    return callback

main()