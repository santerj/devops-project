import pytest
import requests
import redis

import logging

APIGW = "http://api-gw:8083"
HTTPSERV = "http://httpserver:80"

@pytest.fixture
def get_run_log():
    headers = {
        "Content-Type": "text/plain",
        "Accept": "text/plain"
    }
    return requests.get(f"{APIGW}/run-log", headers=headers)

def test_run_log_content_type(get_run_log):
    assert "text/plain" in get_run_log.headers['Content-Type'].split(";")

def test_run_log_content(get_run_log):
    with open(file="/tmp/state-log.txt", mode="r", encoding="utf-8") as file:
        assert file.read() == get_run_log.text
