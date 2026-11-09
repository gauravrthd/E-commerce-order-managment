
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from schema.order_schema import (
    OrderCreate, OrderUpdate, OrderResponse
)
from utils.store import db, next_id
from utils.dependencies import (
    get_current_user, allow_roles,
    get_order_items, can_manage_order
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(
    order: OrderCreate,
    user=Depends(allow_roles("customer"))
):
    if order.user_id != user["id"]:
        raise HTTPException(403, "Cannot place another user's order")

    cart_items = [
        item for item in db["cart"].values()
        if item["user_id"] == user["id"]
    ]

    if not cart_items:
        raise HTTPException(400, "Cart is empty")

    total = 0

    # Validate all products and stock before creating the order.
    for item in cart_items:
        product = db["products"].get(item["product_id"])

        if not product:
            raise HTTPException(404, "Product not found")

        if item["quantity"] > product["stock"]:
            raise HTTPException(400, "Insufficient stock")

        total += product["price"] * item["quantity"]

    order_id = next_id("orders")

    new_order = {
        "id": order_id,
        "user_id": user["id"],
        "total_amount": round(total, 2),
        "shipping_address": order.shipping_address,
        "order_status": "pending",
        "created_at": datetime.now(timezone.utc)
    }

    db["orders"][order_id] = new_order

    for item in cart_items:
        product = db["products"][item["product_id"]]

        order_item_id = next_id("order_items")

        db["order_items"][order_item_id] = {
            "id": order_item_id,
            "order_id": order_id,
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "price": product["price"]
        }

        product["stock"] -= item["quantity"]
        del db["cart"][item["id"]]

    return new_order


@router.get("/", response_model=list[OrderResponse])
def get_orders(user=Depends(get_current_user)):
    orders = list(db["orders"].values())

    if user["role"] == "admin":
        return orders

    if user["role"] == "customer":
        return [
            o for o in orders
            if o["user_id"] == user["id"]
        ]

    if user["role"] == "shopkeeper":
        return [
            o for o in orders
            if any(
                db["products"].get(
                    item["product_id"], {}
                ).get("seller_id") == user["id"]
                for item in get_order_items(o["id"])
            )
        ]

    return []


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, user=Depends(get_current_user)):
    order = db["orders"].get(order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    if user["role"] == "customer":
        if order["user_id"] != user["id"]:
            raise HTTPException(403, "Access denied")

    elif user["role"] == "shopkeeper":
        has_product = any(
            db["products"].get(
                item["product_id"], {}
            ).get("seller_id") == user["id"]
            for item in get_order_items(order_id)
        )

        if not has_product:
            raise HTTPException(403, "Access denied")

    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderUpdate,
    user=Depends(allow_roles("shopkeeper", "admin"))
):
    order = db["orders"].get(order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    if not can_manage_order(user, order_id):
        raise HTTPException(403, "Cannot manage this order")

    new_status = data.order_status

    if new_status is None:
        raise HTTPException(400, "Order status is required")

    allowed_transitions = {
        "pending": "confirmed",
        "confirmed": "shipped",
        "shipped": "delivered"
    }

    current_status = order["order_status"]

    if allowed_transitions.get(current_status) != new_status:
        raise HTTPException(
            400,
            f"Cannot change order from {current_status} to {new_status}"
        )

    order["order_status"] = new_status

    return order
