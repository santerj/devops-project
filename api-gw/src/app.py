import logging
import os
import sys
import time

from common import pollRabbitmqReadiness, initRabbitmqConnection

import pika


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

