
from fastapi import APIRouter, Depends, HTTPException

from schema.order_item_schema import OrderItemResponse
from utils.store import db
from utils.dependencies import (
    get_current_user, get_order_items
)

router = APIRouter(prefix="/order-items", tags=["Order Items"])


@router.get("/{order_id}", response_model=list[OrderItemResponse])
def get_items_by_order(
    order_id: int,
    user=Depends(get_current_user)
):
    order = db["orders"].get(order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    items = get_order_items(order_id)

    if user["role"] == "admin":
        return items

    if user["role"] == "customer":
        if order["user_id"] != user["id"]:
            raise HTTPException(403, "Access denied")

        return items

    if user["role"] == "shopkeeper":
        seller_items = [
            item for item in items
            if db["products"].get(
                item["product_id"], {}
            ).get("seller_id") == user["id"]
        ]

        if not seller_items:
            raise HTTPException(403, "Access denied")

        return seller_items

    raise HTTPException(403, "Access denied")
