import logging
import os
import sys
import time

from common import pollRabbitmqReadiness, initRabbitmqConnection, initRedisConnection

import pika
import redis


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

REDIS_HOST = os.environ.get('REDIS_HOST')
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')


def main():
    r = initRedisConnection(REDIS_HOST)

main()