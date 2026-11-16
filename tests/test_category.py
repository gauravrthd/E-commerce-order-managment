
def test_create_category_as_admin(client, admin, mock_login):
    mock_login(admin)

    response = client.post(
        "/categories/",
        json={
            "name": "Electronics",
            "description": "Electronic products"
        }
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Electronics"


def test_create_category_as_customer(
    client, customer, mock_login
):
    mock_login(customer)

    response = client.post(
        "/categories/",
        json={
            "name": "Electronics",
            "description": "Electronic products"
        }
    )

    assert response.status_code == 403


def test_get_categories(client):
    response = client.get("/categories/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_category_not_found(client):
    response = client.get("/categories/999999")

    assert response.status_code == 404
