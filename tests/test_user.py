
from sqlalchemy import select
from models.user_model import User


def test_register_customer(client, db_session):
    data = {
        "name": "New Customer",
        "email": "newcustomer@test.com",
        "mobile": "9876543210",
        "password": "Secure@12345"
    }

    response = client.post("/users/register", json=data)

    assert response.status_code == 201
    assert response.json()["email"] == data["email"]
    assert response.json()["role"] == "customer"
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()

    user = db_session.scalar(
        select(User).where(User.email == data["email"])
    )

    assert user is not None
    assert user.hashed_password != data["password"]
    assert user.hashed_password.startswith("$argon2")


def test_duplicate_email(client):
    data = {
        "name": "New Customer",
        "email": "duplicate@test.com",
        "mobile": "9876543210",
        "password": "Secure@12345"
    }

    first_response = client.post("/users/register", json=data)
    second_response = client.post("/users/register", json=data)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_invalid_email(client):
    data = {
        "name": "New Customer",
        "email": "invalid-email",
        "mobile": "9876543210",
        "password": "Secure@12345"
    }

    response = client.post("/users/register", json=data)

    assert response.status_code == 422


def test_short_password(client):
    data = {
        "name": "New Customer",
        "email": "short@test.com",
        "mobile": "9876543210",
        "password": "123"
    }

    response = client.post("/users/register", json=data)

    assert response.status_code == 422
