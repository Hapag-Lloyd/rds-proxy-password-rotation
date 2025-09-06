import requests

def test_api_post():
    url = "https://api.example.com/resource"
    payload = {
        "name": "example",
        "value": 42
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data.get("name") == "example"
    assert data.get("value") == 42
