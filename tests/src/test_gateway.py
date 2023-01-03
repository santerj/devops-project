import pytest
import requests

API_HOST = "http://localhost:8083"
HTTPSERV = "http://localhost:8080"

@pytest.fixture
def get_messages():
    headers = {
        "Content-Type": "text/plain",
        "Accept": "text/plain"
    }
    return requests.get(API_HOST, headers=headers)

def test_messages_code(get_messages):
    assert get_messages.status_code == 200

def test_messages_content_type(get_messages):
    assert get_messages.headers['Content-Type'] == "text/plain"

def test_messages_payload(get_messages):
    r = requests.get(HTTPSERV)
    assert r.text == get_messages.text

def test_messages_wrong_method():
    r = requests.put(API_HOST)
    assert r.status_code == 405
