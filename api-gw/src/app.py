import logging
import os
import sys
import time

from common import pollRabbitmqReadiness, initRabbitmqConnection, initRedisConnection

import pika
import redis
import requests
from flask import Flask

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

REDIS_HOST = os.environ.get('REDIS_HOST')
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')


app = Flask(__name__)
r = initRedisConnection(REDIS_HOST)

@app.route("/messages")
def messages():
    r = requests.get("http://httpserv:18080")
    text = r.text
    return text
