
from models.category_model import Category
from models.product_model import Product


def test_add_product_to_cart(
    client, db_session, customer, shopkeeper, mock_login
):
    category = Category(
        name="Footwear",
        description="Shoes"
    )

    db_session.add(category)
    db_session.flush()

    product = Product(
        name="Sports Shoes",
        description="Running shoes",
        price=1500,
        stock=20,
        category_id=category.id,
        seller_id=shopkeeper.id
    )

    db_session.add(product)
    db_session.flush()

    mock_login(customer)

    response = client.post(
        "/cart/",
        json={
            "user_id": customer.id,
            "product_id": product.id,
            "quantity": 2
        }
    )

    assert response.status_code == 201
    assert response.json()["quantity"] == 2


def test_shopkeeper_cannot_use_cart(
    client, shopkeeper, mock_login
):
    mock_login(shopkeeper)

    response = client.get("/cart/")

    assert response.status_code == 403
