import logging
import os
import sys
import time

import pika
import requests


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS')
SUB_TOPIC = os.environ.get('SUB_TOPIC')
PUB_TOPIC = os.environ.get('PUB_TOPIC')


def main():
    # wait until RabbitMQ service is ready, init connection
    pollRabbitmqReadiness(host=RABBITMQ_HOST)
    conn = initRabbitmqConnection(RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS)
    subChannel = conn.channel()
    pubChannel = conn.channel()
    subChannel.queue_declare(queue=SUB_TOPIC, durable=True)
    pubChannel.queue_declare(queue=PUB_TOPIC, durable=True)

    callback = generateCallback(subChannel)
    subChannel.basic_consume(queue=SUB_TOPIC,
                    on_message_callback=callback) 
    subChannel.start_consuming()

def generateCallback(pubChannel: pika.channel.Channel):
    """Wraps actual consumer callback in order to inject extra arguments"""
    def callback(channel: pika.channel.Channel,
            method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties,
            body: bytes):
        """Send message to $PUB_TOPIC upon receiving message from $SUB_TOPIC."""
        logging.info(f"Received message from {SUB_TOPIC}")
        bodyAsString = body.decode()
        pubChannel.basic_publish(exchange='', routing_key=PUB_TOPIC, body=f'Got {bodyAsString}',
                                  properties=pika.BasicProperties(content_type="text/plain"))
        logging.info(f"Published message to {PUB_TOPIC}")
        time.sleep(1)
    return callback

def pollRabbitmqReadiness(host: str) -> None:
    timeout_seconds = 5
    retry_seconds = 5
    retries = 5
    logging.info("Checking RabbitMQ readiness...")
    for i in range(retries):
        try:
            r = requests.get(f"http://{RABBITMQ_HOST}:15692/metrics", timeout=timeout_seconds)
            if r.status_code == 200:
                logging.info("✅ RabbitMQ ready")
                return
        except requests.exceptions.ConnectionError:
            logging.info(f"❌ RabbitMQ not ready, retrying in {retry_seconds} s ({i+1}/{retries})")
            time.sleep(retry_seconds)
    logging.error("RabbitMQ too slow to start")
    exit(1)

def initRabbitmqConnection(host: str, user: str, passwd: str) -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(username=RABBITMQ_USER, password=RABBITMQ_PASS)
    return pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))

main()
