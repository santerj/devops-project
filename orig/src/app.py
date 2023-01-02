import logging
import os
import sys
import time

from common import pollRabbitmqReadiness, initRabbitmqConnection

import pika


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Read configuration from environment variables
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS')
EXCHANGE = os.environ.get('EXCHANGE')
ROUTING_KEY = os.environ.get('ROUTING_KEY')
TEST_QUEUE = os.environ.get('TEST_QUEUE')


def main():
    # wait until RabbitMQ service is ready, init connection
    pollRabbitmqReadiness(host=RABBITMQ_HOST)
    conn = initRabbitmqConnection(RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS)
    
    # Try passive queue declares until queue exists (listener is ready)
    logging.info("Checking for queue readiness...")
    while True:
        try:
            channel = conn.channel()
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic")
            channel.queue_declare(queue=TEST_QUEUE, passive=True)
            logging.info(f"✅ Queue {TEST_QUEUE} found, starting!")
            break
        except pika.exceptions.ChannelClosedByBroker:
            logging.info(f"❌ Queue {TEST_QUEUE} not ready, retrying...")
            conn.sleep(1)

    n = 1
    while True:
        # publish 3 messages
        msg = f"MSG_{str(n)}"
        channel.basic_publish(exchange=EXCHANGE, routing_key=ROUTING_KEY, body=msg,
                              properties=pika.BasicProperties(content_type="text/plain"))
        logging.info(f"Published message to {EXCHANGE}.{ROUTING_KEY}")
        n += 1
        conn.sleep(3)

    logging.info("Idling...")
    while True:
        # Stay idle until termination
        conn.sleep(60)

main()
