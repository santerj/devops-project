import logging
import os
import sys
import time

from common import pollRabbitmqReadiness, initRabbitmqConnection, initRedisConnection

import pika
import redis


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Read configuration from environment variables
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS')
EXCHANGE = os.environ.get('EXCHANGE')
ROUTING_KEY = os.environ.get('ROUTING_KEY')
TEST_QUEUE = os.environ.get('TEST_QUEUE')
REDIS_HOST = os.environ.get('REDIS_HOST')


def main():
    # wait until RabbitMQ service is ready, init connection
    pollRabbitmqReadiness(host=RABBITMQ_HOST)
    rabbitmq_conn = initRabbitmqConnection(RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS)
    redis_conn = initRedisConnection(REDIS_HOST)
    #redis_conn.set("state", "RUNNING")  # initial value
    
    # Try passive queue declares until queue exists (listener is ready)
    logging.info("Checking for queue readiness...")
    while True:
        try:
            channel = rabbitmq_conn.channel()
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic")
            channel.queue_declare(queue=TEST_QUEUE, passive=True)
            logging.info(f"✅ Queue {TEST_QUEUE} found, starting!")
            break
        except pika.exceptions.ChannelClosedByBroker:
            logging.info(f"❌ Queue {TEST_QUEUE} not ready, retrying...")
            rabbitmq_conn.sleep(1)

    n = 1
    while True:

        # check Redis for state
        state = redis_conn.get("state").decode()

        if state == "RUNNING":
            # publish messages
            msg = f"MSG_{str(n)}"
            channel.basic_publish(exchange=EXCHANGE, routing_key=ROUTING_KEY, body=msg,
                                properties=pika.BasicProperties(content_type="text/plain"))
            logging.info(f"Published message to {EXCHANGE}.{ROUTING_KEY}")
            n += 1
        elif state == "PAUSED":
            pass
        elif state == "SHUTDOWN":
            logging.critical("Received SHUTDOWN, exiting")
            # push one last message to RabbitMQ to relay the shutdown event
            # to imed and obse – their shutdown logic is in the consumer function
            channel.basic_publish(exchange=EXCHANGE, routing_key=ROUTING_KEY, body="",
                              properties=pika.BasicProperties(content_type="text/plain"))
            sys.exit(0)
        rabbitmq_conn.sleep(3)

main()
