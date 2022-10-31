import logging
import os
import time

import pika
import requests


def main():
    host = os.environ.get('RABBITMQ_HOST')
    username = os.environ.get('RABBITMQ_USER')
    password = os.environ.get('RABBITMQ_PASS')
    pollRabbitmqReadiness(host=host)
    credentials = pika.PlainCredentials(username=username, password=password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))
    channel = connection.channel()

    # testing
    channel.exchange_declare('test', durable=True, exchange_type='topic')
    channel.queue_declare(queue='A')
    channel.queue_bind(exchange='test', queue='A', routing_key='A')
    message = 'Hello World'
    channel.basic_publish(exchange='test', routing_key='A', body= message)
    channel.close()
    while True:
        time.sleep(10000)

def pollRabbitmqReadiness(host: str) -> None:
    timeout_seconds = 5
    retry_seconds = 5
    retries = 5
    logging.warning("Checking RabbitMQ readiness...")
    for i in range(retries):
        try:
            r = requests.get(f"http://{host}:15692/metrics", timeout=timeout_seconds)
            if r.status_code == 200:
                logging.warning("✅ RabbitMQ ready")
                return
        except requests.exceptions.ConnectionError:
            logging.warning(f"❌ RabbitMQ not ready, retrying in {retry_seconds} s ({i+1}/{retries})")
            time.sleep(retry_seconds)
    logging.error("RabbitMQ too slow to start")
    exit(1)

main()
