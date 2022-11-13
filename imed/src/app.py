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
EXCHANGE = os.environ.get('EXCHANGE')
QUEUE = os.environ.get('QUEUE')
ROUTING_KEY_READ = os.environ.get('ROUTING_KEY_READ')
ROUTING_KEY_WRITE = os.environ.get('ROUTING_KEY_WRITE')


def main():
    # wait until RabbitMQ service is ready, init connection
    pollRabbitmqReadiness(host=RABBITMQ_HOST)
    conn = initRabbitmqConnection(RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS)
    channel = conn.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic")
    channel.queue_declare(queue=QUEUE, exclusive=True)
    channel.queue_bind(queue=QUEUE, exchange=EXCHANGE,routing_key=ROUTING_KEY_READ)
    channel.basic_consume(queue=QUEUE, auto_ack=True, on_message_callback=callback)
    channel.start_consuming()
    
def callback(channel: pika.channel.Channel, method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties, body: bytes):
    """Send message to $PUB_TOPIC upon receiving message from $SUB_TOPIC."""
    logging.info(f"Received message from {EXCHANGE}.{ROUTING_KEY_READ}")
    bodyAsString = body.decode()
    msg = f"Got {bodyAsString}"
    channel.basic_publish(exchange=EXCHANGE, routing_key=ROUTING_KEY_WRITE, body=msg,
                                properties=pika.BasicProperties(content_type="text/plain"))
    logging.info(f"Published message to {EXCHANGE}.{ROUTING_KEY_WRITE}")
    time.sleep(1)

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
    credentials = pika.PlainCredentials(username=user, password=passwd)
    return pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))

main()
