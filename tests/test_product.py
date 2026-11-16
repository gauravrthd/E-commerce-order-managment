
from models.category_model import Category
from models.product_model import Product


def test_create_product(
    client, db_session, shopkeeper, mock_login
):
    category = Category(
        name="Electronics",
        description="Electronic items"
    )

    db_session.add(category)
    db_session.flush()

    mock_login(shopkeeper)

    response = client.post(
        "/products/",
        json={
            "name": "Laptop",
            "description": "Dell Laptop",
            "price": 45000,
            "stock": 10,
            "category_id": category.id,
            "seller_id": shopkeeper.id
        }
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Laptop"
    assert response.json()["stock"] == 10

    product = db_session.get(
        Product, response.json()["id"]
    )

    assert product is not None
    assert product.seller_id == shopkeeper.id


def test_customer_cannot_create_product(
    client, customer, mock_login
):
    mock_login(customer)

    response = client.post(
        "/products/",
        json={
            "name": "Phone",
            "price": 20000,
            "stock": 5,
            "category_id": 1,
            "seller_id": customer.id
        }
    )

    assert response.status_code == 403


def test_product_not_found(client):
    response = client.get("/products/999999")

    assert response.status_code == 404


def test_invalid_product_price(
    client, shopkeeper, mock_login
):
    mock_login(shopkeeper)

    response = client.post(
        "/products/",
        json={
            "name": "Laptop",
            "price": -100,
            "stock": 10,
            "category_id": 1,
            "seller_id": shopkeeper.id
        }
    )

    assert response.status_code == 422
