from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "Temperature Converter" in r.json()["message"]


def test_celsius_to_fahrenheit():
    r = client.get("/convert", params={"value": 0, "from": "celsius", "to": "fahrenheit"})
    assert r.status_code == 200
    assert r.json()["output"]["value"] == 32.0


def test_celsius_to_kelvin():
    r = client.get("/convert", params={"value": 100, "from": "celsius", "to": "kelvin"})
    assert r.status_code == 200
    # 100°C = 373.15K
    assert round(r.json()["output"]["value"], 2) == 373.15


def test_fahrenheit_to_celsius():
    r = client.get("/convert", params={"value": 32, "from": "fahrenheit", "to": "celsius"})
    assert r.status_code == 200
    assert round(r.json()["output"]["value"], 6) == 0.0


def test_invalid_unit_returns_422():
    r = client.get("/convert", params={"value": 10, "from": "banana", "to": "celsius"})
    assert r.status_code == 422


def test_missing_param_returns_422():
    r = client.get("/convert", params={"value": 10, "from": "celsius"})
    assert r.status_code == 422
