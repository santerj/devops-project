import pytest
import requests

APIGW = "http://api-gw:8083"
HTTPSERV = "http://httpserver:80"

@pytest.fixture
def get_state():
    headers = {
        "Content-Type": "text/plain",
        "Accept": "text/plain"
    }
    return requests.get(f"{APIGW}/messages", headers=headers)

## /state

def test_state_code(get_state):
    assert get_state.status_code == 200

def test_state_content_type(get_state):
    assert get_state.headers['Content-Type'] == "text/plain"

def test_state_content(get_state):
    assert get_state.text in ("INIT", "PAUSED", "RUNNING", "SHUTDOWN")

def test_state_wrong_methods():
    r = requests.patch(f"{APIGW}/state")
    assert r.status_code == 405
    r = requests.delete(f"{APIGW}/state")
    assert r.status_code == 405

def test_state_put(get_state):
    state = "RUNNING"
    r1 = requests.put(f"{APIGW}/state", data={'state': state})
    assert r1.status_code == 200
    assert get_state.text == state
    # TODO: check from redis as well
