import os
import time

import pika


def main():
    host = os.environ.get('RABBITMQ_HOST')
    username = os.environ.get('RABBITMQ_USER')
    password = os.environ.get('RABBITMQ_PASS')
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

main()