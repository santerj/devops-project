import logging
import time

import pika
import requests
import redis


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

def initRabbitmqConnection(host: str, user: str, passwd: str) -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(username=user, password=passwd)
    return pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))

def initRedisConnection(host: str, port: int=6379, db: int=0) -> redis.client.Redis:
    retries = 5
    retry_seconds = 1
    for i in range(retries):
        try:
            r = redis.Redis(host=host, port=port, db=db)
            logging.info("✅ Connection to Redis established")
            return r
        except redis.exceptions.ConnectionError:
            logging.info(f"❌ Connection to Redis not established, retrying in {retry_seconds} s ({i+1}/{retries})")
            time.sleep(retry_seconds)
    logging.error("Connection to Redis can't be established")
    exit(1)
