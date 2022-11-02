import logging
import os
import time
import sys

import pika
import requests


def main():
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    host = os.environ.get('RABBITMQ_HOST')
    username = os.environ.get('RABBITMQ_USER')
    password = os.environ.get('RABBITMQ_PASS')

    # wait until RabbitMQ service is ready, init connection
    pollRabbitmqReadiness(host=host)
    conn = initRabbitmqConnection(host, username, password)
    channel_o = conn.channel()
    channel_i = conn.channel()
    channel_o.queue_declare(queue='compse140.o', durable=True)
    channel_i.queue_declare(queue='compse140.i', durable=True)

    callback = generateCallback(channel_o)
    channel_o.basic_consume(queue='compse140.o',
                    auto_ack=True,
                    on_message_callback=callback)
    channel_o.start_consuming()  # service listens to

def generateCallback(pubChannel: pika.channel.Channel):
    """Wraps actual consumer callback in order to inject extra arguments"""
    def callback(channel: pika.channel.Channel,
            method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties,
            body: bytes):
        """Send message to 'compse140.i' upon receiving message from 'compse140.o'."""
        logging.info(f"Received message {body}")
        bodyAsString = body.decode()
        pubChannel.basic_publish(exchange='', routing_key='compse140.i', body=f'Got {bodyAsString}',
                                  properties=pika.BasicProperties(content_type="text/plain"))
        logging.info("Published message")
        time.sleep(1)
    return callback

def pollRabbitmqReadiness(host: str) -> None:
    timeout_seconds = 5
    retry_seconds = 5
    retries = 5
    logging.info("Checking RabbitMQ readiness...")
    for i in range(retries):
        try:
            r = requests.get(f"http://{host}:15692/metrics", timeout=timeout_seconds)
            if r.status_code == 200:
                logging.info("✅ RabbitMQ ready")
                return
        except requests.exceptions.ConnectionError:
            logging.info(f"❌ RabbitMQ not ready, retrying in {retry_seconds} s ({i+1}/{retries})")
            time.sleep(retry_seconds)
    logging.error("RabbitMQ too slow to start")
    exit(1)

def initRabbitmqConnection(host: str, username: str, password: str) -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(username=username, password=password)
    return pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))

main()
