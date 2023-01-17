import logging
import os
import subprocess
import signal
import sys
import time

from datetime import datetime, timezone

from common import pollRabbitmqReadiness, initRabbitmqConnection, initRedisConnection

import pika
import redis
import requests
from flask import Flask, Response, request

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

REDIS_HOST = os.environ.get('REDIS_HOST')
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
NGINX_HOST = os.environ.get('NGINX_HOST')
FILE = os.environ.get('FILE')

# initializers
app = Flask(__name__)
r = initRedisConnection(REDIS_HOST)
r.set("state", "RUNNING")
with open(file=FILE, mode="w") as f:
    logging.info(f"Flushing {FILE}")
    f.close()


@app.route("/messages")
def messages():
    req = requests.get(f"http://{NGINX_HOST}")
    text = req.text
    return Response(text, mimetype="text/plain", status=200)

@app.route("/state", methods=["GET", "PUT"])
def state():

    if request.method == "GET":
        state = r.get("state").decode()
        return Response(state, mimetype="text/plain")
    
    elif request.method == "PUT":
        state = request.form.get("state")
        
        if state not in ("INIT", "PAUSED", "RUNNING", "SHUTDOWN"):
            return Response("Bad request", status=400, mimetype="text/plain")
        else:
            r.set("state", state)
            # write to log file
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S:%f")[:-3]+"Z"
            msg = f"{timestamp}: {state}\n"
            with open(file=FILE, mode="a", encoding="utf-8") as file:
                    file.write(msg)
                    file.close()

            response = Response("OK", status=200, mimetype="text/plain")
            
            @response.call_on_close
            def on_close():
                if state == "SHUTDOWN":
                    logging.critical("Received SHUTDOWN, exiting")
                    os.kill(os.getpid(), signal.SIGINT)
            
            return response

@app.route("/run-log")
def run_log():
    with open(file=FILE, mode="r", encoding="utf-8") as file:
        text = file.read()
        file.close()
    return Response(text, mimetype="text/plain", status=200)
