
from models.category_model import Category
from models.product_model import Product
from models.cart_model import Cart
from models.order_model import Order
from models.order_item_model import OrderItem

import routers.order_router as order_router


def test_create_order(
    client,
    db_session,
    customer,
    shopkeeper,
    mock_login,
    monkeypatch
):
    notifications = []

    def fake_confirmation(email, order_id, amount):
        notifications.append((email, order_id, amount))

    monkeypatch.setattr(
        order_router,
        "send_order_confirmation",
        fake_confirmation
    )

    category = Category(
        name="Furniture",
        description="Home furniture"
    )

    db_session.add(category)
    db_session.flush()

    product = Product(
        name="Office Chair",
        description="Comfortable chair",
        price=3000,
        stock=10,
        category_id=category.id,
        seller_id=shopkeeper.id
    )

    db_session.add(product)
    db_session.flush()

    cart = Cart(
        user_id=customer.id,
        product_id=product.id,
        quantity=2
    )

    db_session.add(cart)
    db_session.flush()

    mock_login(customer)

    response = client.post(
        "/orders/",
        json={
            "user_id": customer.id,
            "total_amount": 0,
            "shipping_address": "Indore, Madhya Pradesh",
            "order_status": "pending"
        }
    )

    assert response.status_code == 201

    result = response.json()
    order_id = result["id"]

    assert float(result["total_amount"]) == 6000
    assert result["order_status"] == "pending"

    order = db_session.get(Order, order_id)
    assert order is not None

    db_session.refresh(product)
    assert product.stock == 8

    items = db_session.query(OrderItem).filter(
        OrderItem.order_id == order_id
    ).all()

    assert len(items) == 1
    assert items[0].quantity == 2

    assert len(notifications) == 1
    assert notifications[0][1] == order_id


def test_empty_cart_order(
    client, customer, mock_login
):
    mock_login(customer)

    response = client.post(
        "/orders/",
        json={
            "user_id": customer.id,
            "total_amount": 0,
            "shipping_address": "Indore",
            "order_status": "pending"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart is empty"
