import pytest
import requests

APIGW = "http://api-gw:8083"
HTTPSERV = "http://httpserver:80"

@pytest.fixture
def get_messages():
    headers = {
        "Content-Type": "text/plain",
        "Accept": "text/plain"
    }
    return requests.get(f"{APIGW}/messages", headers=headers)

## /messages

def test_messages_code(get_messages):
    assert get_messages.status_code == 200

def test_messages_content_type(get_messages):
    assert "text/plain" in get_messages.headers['Content-Type'].split(";")

def test_messages_payload(get_messages):
    # checks that gateway returns the same content as httpserver
    r = requests.get(HTTPSERV)
    assert r.text == get_messages.text

def test_messages_wrong_methods():
    r = requests.put(f"{APIGW}/messages")
    assert r.status_code == 405
    r = requests.delete(f"{APIGW}/messages")
    assert r.status_code == 405
