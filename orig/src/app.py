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
PUB_TOPIC = os.environ.get('PUB_TOPIC')


def main():
    # wait until RabbitMQ service is ready, init connection
    pollRabbitmqReadiness(host=RABBITMQ_HOST)
    conn = initRabbitmqConnection(RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS)
    channel = conn.channel()
    channel.exchange_declare(exchange="compse140", exchange_type="topic")

    conn.sleep(5)

    for n in range(3):
        # publish 3 messages
        msg = f"MSG_{str(n+1)}"
        channel.basic_publish(exchange='compse140', routing_key="o", body=msg,
                              properties=pika.BasicProperties(content_type="text/plain"))
        logging.info(f"Published message")
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
    credentials = pika.PlainCredentials(username=RABBITMQ_USER, password=RABBITMQ_PASS)
    return pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))

main()
