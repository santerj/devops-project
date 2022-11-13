import logging
import os
import sys
import time
import typing

from datetime import datetime, timezone

import pika
import requests


logging.basicConfig(stream=sys.stderr, level=logging.INFO)


RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS')
SUB_TOPIC_1 = os.environ.get('SUB_TOPIC_1')
SUB_TOPIC_2 = os.environ.get('SUB_TOPIC_2')

class Counter:
    def __init__(self) -> None:
        self.number = 1

def main():
    # wait until RabbitMQ service is ready, init connection
    pollRabbitmqReadiness(host=RABBITMQ_HOST)
    conn = initRabbitmqConnection(RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS)
    
    # flush file
    with open(file="/opt/data/log.txt", mode="w") as f:
        f.close()
    counter = Counter()

    channel = conn.channel()
    channel.exchange_declare(exchange="compse140", exchange_type="topic")
    channel.queue_declare(queue="obse_queue_o", exclusive=True)
    channel.queue_declare(queue="obse_queue_i", exclusive=True)
    channel.queue_bind(queue="obse_queue_o", exchange="compse140", routing_key="o")
    channel.queue_bind(queue="obse_queue_i", exchange="compse140", routing_key="i")
    channel.basic_consume(queue="obse_queue_o", auto_ack=True, on_message_callback=generateCallback("compse140.o", counter, filename="/opt/data/log.txt"))
    channel.basic_consume(queue="obse_queue_i", auto_ack=True, on_message_callback=generateCallback("compse140.i", counter, filename="/opt/data/log.txt"))
    channel.start_consuming()


def generateCallback(topic: str, counter: Counter, filename: str):
    def callback(channel: pika.channel.Channel, method: pika.spec.Basic.Deliver,
                properties: pika.spec.BasicProperties, body: bytes):
            bodyAsString = body.decode()
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S:%fZ")
            msg = f"{timestamp} {counter.number} {bodyAsString} to {topic}\n"
            logging.info(msg)
            with open(file=filename, mode="a", encoding="utf-8") as file:
                file.write(msg)
                file.close()
            counter.number += 1
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