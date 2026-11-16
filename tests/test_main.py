
def test_welcome(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to my E-Commerce Order Management System!"
    }


def test_invalid_endpoint(client):
    response = client.get("/invalid-endpoint")

    assert response.status_code == 404
