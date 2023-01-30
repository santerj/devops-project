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
    return requests.get(f"{APIGW}/run-log", headers=headers)

def test_run_log_code(get_run_log):
    assert get_run_log.status_code == 200

def test_run_log_content_type(get_run_log):
    assert "text/plain" in get_run_log.headers['Content-Type'].split(";")

def test_run_log_content():
    # first, make a couple PUT requests to /state
    series = ["RUNNING", "INIT", "RUNNING", "PAUSED", "RUNNING"]
    headers = {
        "Content-Type": "text/plain",
        "Accept": "text/plain"
    }
    for state in series:
        requests.put(f"{APIGW}/state", data=state, headers=
                     {"Content-Type": "text/plain", "Accept": "text/plain"})

    # next, ensure that the state has changed in the same order
    log_parts = requests.get(f"{APIGW}/run-log", headers=headers).text.split("\n")
    
    # strip out empty lines
    log_parts = [line for line in log_parts if line != ""]
    
    assert len(series) == len(log_parts)
    for i, line in enumerate(log_parts):
        state = line.split(" ")[-1]  # leave out timestamp
        assert state == series[i]
