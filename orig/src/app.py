import logging
import os
import time

import pika
import requests


def main():
    host = os.environ.get('RABBITMQ_HOST')
    username = os.environ.get('RABBITMQ_USER')
    password = os.environ.get('RABBITMQ_PASS')

    # wait until RabbitMQ service is ready
    pollRabbitmqReadiness(host=host)
    conn = initRabbitmqConnection(host, username, password)
    channel = conn.channel()
    channel.queue_declare(queue='compse140.o')

    for n in range(3):
        channel.basic_publish(exchange='', routing_key='compse140.o', body=f'MSG_{{n+1}}')
        time.sleep(3)

    
    
    channel.close()

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

def initRabbitmqConnection(host: str, username: str, password: str) -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(username=username, password=password)
    return pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))

main()
