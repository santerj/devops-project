import logging
import os
import sys
import time

import pika
import requests


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Read configuration from environment variables
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS')
EXCHANGE = os.environ.get('EXCHANGE')
ROUTING_KEY = os.environ.get('ROUTING_KEY')


def main():
    # wait until RabbitMQ service is ready, init connection
    pollRabbitmqReadiness(host=RABBITMQ_HOST)
    conn = initRabbitmqConnection(RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS)

    # Setup messaging
    channel = conn.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic")

    # Probably will be a reduction in points, but imed and obse are (sometimes)
    # too slow to start and will miss the first message. Sleeping fixes this but is not
    # an elegant solution.
    conn.sleep(3)

    for n in range(3):
        # publish 3 messages
        msg = f"MSG_{str(n+1)}"
        channel.basic_publish(exchange=EXCHANGE, routing_key=ROUTING_KEY, body=msg,
                              properties=pika.BasicProperties(content_type="text/plain"))
        logging.info(f"Published message to {EXCHANGE}.{ROUTING_KEY}")
        conn.sleep(3)

    logging.info("Idling...")
    while True:
        # Stay idle until termination
        conn.sleep(60)

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
