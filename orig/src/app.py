import logging
import os
import time
import sys

import pika
import requests


def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    host = os.environ.get('RABBITMQ_HOST')
    username = os.environ.get('RABBITMQ_USER')
    password = os.environ.get('RABBITMQ_PASS')

    # wait until RabbitMQ service is ready, init connection
    pollRabbitmqReadiness(host=host)
    conn = initRabbitmqConnection(host, username, password)
    channel = conn.channel()
    channel.queue_declare(queue='compse140.o')

    for n in range(3):
        # publish 3 messages
        channel.basic_publish(exchange='', routing_key='compse140.o', body=f'MSG_{{n+1}}')
        logging.info("Published message")
        time.sleep(3)

    while True:
        # idle
        logging.info("Idling...")
        conn.sleep(60)

def pollRabbitmqReadiness(host: str) -> None:
    timeout_seconds = 5
    retry_seconds = 5
    retries = 5
    logging.debug("Checking RabbitMQ readiness...")
    for i in range(retries):
        try:
            r = requests.get(f"http://{host}:15692/metrics", timeout=timeout_seconds)
            if r.status_code == 200:
                logging.info("✅ RabbitMQ ready")
                return
        except requests.exceptions.ConnectionError:
            logging.debug(f"❌ RabbitMQ not ready, retrying in {retry_seconds} s ({i+1}/{retries})")
            time.sleep(retry_seconds)
    logging.error("RabbitMQ too slow to start")
    exit(1)

def initRabbitmqConnection(host: str, username: str, password: str) -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(username=username, password=password)
    return pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))

main()
