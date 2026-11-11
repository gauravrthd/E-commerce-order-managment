
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user_model import User
from models.order_model import Order
from models.order_item_model import OrderItem
from models.product_model import Product
from schema.order_item_schema import OrderItemResponse
from utils.dependencies import get_current_user

router = APIRouter(prefix="/order-items", tags=["Order Items"])


@router.get("/{order_id}", response_model=list[OrderItemResponse])
def get_order_items(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = db.get(Order, order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    if user.role == "customer":
        if order.user_id != user.id:
            raise HTTPException(403, "Access denied")

        return db.scalars(
            select(OrderItem).where(OrderItem.order_id == order_id)
        ).all()

    if user.role == "shopkeeper":
        items = db.scalars(
            select(OrderItem)
            .join(Product, Product.id == OrderItem.product_id)
            .where(
                OrderItem.order_id == order_id,
                Product.seller_id == user.id
            )
        ).all()

        if not items:
            raise HTTPException(403, "Access denied")

        return items

    if user.role == "admin":
        return db.scalars(
            select(OrderItem).where(OrderItem.order_id == order_id)
        ).all()

    raise HTTPException(403, "Access denied")
