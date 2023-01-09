import pytest
import requests
import redis


APIGW = "http://api-gw:8083"
HTTPSERV = "http://httpserver:80"

@pytest.fixture
def get_run_log():
    headers = {
        "Content-Type": "text/plain",
        "Accept": "text/plain"
    }
    return requests.get(f"{APIGW}/state", headers=headers)
