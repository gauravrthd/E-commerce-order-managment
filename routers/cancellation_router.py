
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.connection import get_db
from models.user_model import User
from models.order_model import Order
from models.order_item_model import OrderItem
from models.product_model import Product
from models.cancellation_model import Cancellation
from models.payment_model import Payment
from schema.cancellation_schema import (
    CancellationCreate, CancellationUpdate, CancellationResponse
)
from utils.dependencies import get_current_user, allow_roles

router = APIRouter(
    prefix="/cancellations",
    tags=["Cancellations"]
)


@router.post("/", response_model=CancellationResponse, status_code=201)
def request_cancellation(
    data: CancellationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("customer"))
):
    order = db.get(Order, data.order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    if order.user_id != user.id:
        raise HTTPException(403, "Access denied")

    if order.order_status not in ["pending", "confirmed"]:
        raise HTTPException(400, "Order cannot be cancelled")

    existing = db.scalar(
        select(Cancellation).where(
            Cancellation.order_id == data.order_id
        )
    )

    if existing:
        raise HTTPException(409, "Cancellation already requested")

    payment = db.scalar(
        select(Payment).where(Payment.order_id == data.order_id)
    )

    if payment and payment.payment_status == "success":
        raise HTTPException(409, "Paid order requires refund handling")

    cancellation = Cancellation(
        order_id=data.order_id,
        reason=data.reason,
        cancellation_status="pending"
    )

    db.add(cancellation)

    try:
        db.commit()
        db.refresh(cancellation)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Cancellation already exists")

    return cancellation


@router.get("/", response_model=list[CancellationResponse])
def get_cancellations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role == "admin":
        query = select(Cancellation)

    elif user.role == "customer":
        query = (
            select(Cancellation)
            .join(Order, Order.id == Cancellation.order_id)
            .where(Order.user_id == user.id)
        )

    else:
        raise HTTPException(403, "Access denied")

    return db.scalars(query).all()


@router.get("/{cancellation_id}", response_model=CancellationResponse)
def get_cancellation(
    cancellation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    cancellation = db.get(Cancellation, cancellation_id)

    if not cancellation:
        raise HTTPException(404, "Cancellation not found")

    order = db.get(Order, cancellation.order_id)

    if user.role != "admin" and order.user_id != user.id:
        raise HTTPException(403, "Access denied")

    return cancellation


@router.patch("/{cancellation_id}", response_model=CancellationResponse)
def update_cancellation(
    cancellation_id: int,
    data: CancellationUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(allow_roles("admin"))
):
    cancellation = db.scalar(
        select(Cancellation)
        .where(Cancellation.id == cancellation_id)
        .with_for_update()
    )

    if not cancellation:
        raise HTTPException(404, "Cancellation not found")

    if cancellation.cancellation_status != "pending":
        raise HTTPException(400, "Cancellation already processed")

    if data.cancellation_status not in ["approved", "rejected"]:
        raise HTTPException(400, "Invalid cancellation status")

    order = db.scalar(
        select(Order)
        .where(Order.id == cancellation.order_id)
        .with_for_update()
    )

    if data.cancellation_status == "approved":
        if order.order_status not in ["pending", "confirmed"]:
            raise HTTPException(400, "Order cannot be cancelled")

        payment = db.scalar(
            select(Payment)
            .where(Payment.order_id == order.id)
            .with_for_update()
        )

        if payment and payment.payment_status == "success":
            raise HTTPException(409, "Refund handling required")

        items = db.scalars(
            select(OrderItem)
            .where(OrderItem.order_id == order.id)
            .order_by(OrderItem.product_id)
        ).all()

        product_ids = sorted({item.product_id for item in items})

        products = db.scalars(
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update()
        ).all()

        product_map = {product.id: product for product in products}

        for item in items:
            product = product_map.get(item.product_id)

            if not product:
                raise HTTPException(409, "Order product not found")

            product.stock += item.quantity

        order.order_status = "cancelled"

    cancellation.cancellation_status = data.cancellation_status

    db.commit()
    db.refresh(cancellation)

    return cancellation
