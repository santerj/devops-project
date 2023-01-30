import pytest
import requests
import redis


APIGW = "http://api-gw:8083"
HTTPSERV = "http://httpserver:80"

@pytest.fixture
def get_state():
    headers = {
        "Content-Type": "text/plain",
        "Accept": "text/plain"
    }
    return requests.get(f"{APIGW}/state", headers=headers)

@pytest.fixture
def redis_conn():
    return redis.Redis(host="redis", port=6379, db=0)

## /state

def test_state_code(get_state):
    assert get_state.status_code == 200

def test_state_content_type(get_state):
    assert "text/plain" in get_state.headers['Content-Type'].split(";")

def test_state_content(get_state):
    assert get_state.text in ("INIT", "PAUSED", "RUNNING", "SHUTDOWN")

def test_state_wrong_methods():
    r = requests.patch(f"{APIGW}/state")
    assert r.status_code == 405
    r = requests.delete(f"{APIGW}/state")
    assert r.status_code == 405

def test_state_put(get_state):
    target_state = "RUNNING"
    r1 = requests.put(f"{APIGW}/state", data=target_state, headers=
                      {"Content-Type": "text/plain", "Accept": "text/plain"})
    assert r1.status_code == 200  # code for PUT request
    assert get_state.text == target_state

def test_state_put_invalid(get_state):
    original_state = get_state.text
    target_state = "INVALID"
    r1 = requests.put(f"{APIGW}/state", data=target_state, headers=
                      {"Content-Type": "text/plain", "Accept": "text/plain"})
    assert r1.status_code == 400

def test_state_in_redis(get_state, redis_conn):
    state_in_redis = redis_conn.get("state").decode()
    assert get_state.text == state_in_redis

def test_state_put_in_redis(get_state, redis_conn):
    # first, set state to PAUSED
    target_state = "PAUSED"
    r1 = requests.put(f"{APIGW}/state", data=target_state, headers=
                      {"Content-Type": "text/plain", "Accept": "text/plain"})
    assert r1.status_code == 200
    assert redis_conn.get("state").decode() == target_state

    # next, put new state
    target_state = "RUNNING"
    r1 = requests.put(f"{APIGW}/state", data=target_state, headers=
                      {"Content-Type": "text/plain", "Accept": "text/plain"})
    assert r1.status_code == 200
    assert redis_conn.get("state").decode() == target_state
