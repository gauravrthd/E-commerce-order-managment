
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user_model import User
from models.product_model import Product
from models.cart_model import Cart
from models.order_model import Order
from models.order_item_model import OrderItem
from schema.order_schema import (
    OrderCreate, OrderUpdate, OrderResponse
)
from utils.dependencies import get_current_user, allow_roles

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("customer"))
):
    if data.user_id != user.id:
        raise HTTPException(403, "Access denied")

    if not data.shipping_address.strip():
        raise HTTPException(400, "Shipping address is required")

    cart_items = db.scalars(
        select(Cart)
        .where(Cart.user_id == user.id)
        .order_by(Cart.product_id)
        .with_for_update()
    ).all()

    if not cart_items:
        raise HTTPException(400, "Cart is empty")

    product_ids = sorted({item.product_id for item in cart_items})

    products = db.scalars(
        select(Product)
        .where(Product.id.in_(product_ids))
        .order_by(Product.id)
        .with_for_update()
    ).all()

    product_map = {product.id: product for product in products}
    total = Decimal("0.00")

    for item in cart_items:
        product = product_map.get(item.product_id)

        if not product:
            raise HTTPException(404, "Product not found")

        if product.stock < item.quantity:
            raise HTTPException(
                400,
                f"Insufficient stock for {product.name}"
            )

        total += product.price * item.quantity

    order = Order(
        user_id=user.id,
        total_amount=total,
        shipping_address=data.shipping_address,
        order_status="pending"
    )

    try:
        db.add(order)
        db.flush()

        for item in cart_items:
            product = product_map[item.product_id]

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                price=product.price
            )

            product.stock -= item.quantity

            db.add(order_item)
            db.delete(item)

        db.commit()
        db.refresh(order)

    except Exception:
        db.rollback()
        raise

    return order


@router.get("/", response_model=list[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role == "admin":
        query = select(Order)

    elif user.role == "customer":
        query = select(Order).where(Order.user_id == user.id)

    elif user.role == "shopkeeper":
        query = (
            select(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(Product.seller_id == user.id)
            .distinct()
        )

    else:
        raise HTTPException(403, "Access denied")

    return db.scalars(query.order_by(Order.id.desc())).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = db.get(Order, order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    if user.role == "customer" and order.user_id != user.id:
        raise HTTPException(403, "Access denied")

    if user.role == "shopkeeper":
        seller_product = db.scalar(
            select(OrderItem.id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(
                OrderItem.order_id == order_id,
                Product.seller_id == user.id
            )
        )

        if seller_product is None:
            raise HTTPException(403, "Access denied")

    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("shopkeeper", "admin"))
):
    order = db.scalar(
        select(Order)
        .where(Order.id == order_id)
        .with_for_update()
    )

    if not order:
        raise HTTPException(404, "Order not found")

    if user.role == "shopkeeper":
        items = db.scalars(
            select(OrderItem)
            .where(OrderItem.order_id == order_id)
        ).all()

        if not items:
            raise HTTPException(403, "Access denied")

        seller_ids = {
            db.get(Product, item.product_id).seller_id
            for item in items
        }

        if seller_ids != {user.id}:
            raise HTTPException(403, "Cannot manage this order")

    transitions = {
        "pending": "confirmed",
        "confirmed": "shipped",
        "shipped": "delivered"
    }

    if transitions.get(order.order_status) != data.order_status:
        raise HTTPException(400, "Invalid order status change")

    order.order_status = data.order_status

    db.commit()
    db.refresh(order)

    return order
