
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.connection import get_db
from models.user_model import User
from models.order_model import Order
from models.payment_model import Payment
from models.cancellation_model import Cancellation
from schema.payment_schema import (
    PaymentCreate, PaymentUpdate, PaymentResponse
)
from utils.dependencies import get_current_user, allow_roles

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("customer"))
):
    order = db.get(Order, data.order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    if order.user_id != user.id:
        raise HTTPException(403, "Access denied")

    if order.order_status == "cancelled":
        raise HTTPException(400, "Order is cancelled")

    if data.payment_method not in ["upi", "card", "cod"]:
        raise HTTPException(400, "Invalid payment method")

    existing = db.scalar(
        select(Payment).where(Payment.order_id == data.order_id)
    )

    if existing:
        raise HTTPException(409, "Payment already exists")

    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        payment_method=data.payment_method,
        payment_status="pending"
    )

    db.add(payment)

    try:
        db.commit()
        db.refresh(payment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Payment already exists")

    return payment


@router.get("/", response_model=list[PaymentResponse])
def get_payments(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role == "admin":
        query = select(Payment)

    elif user.role == "customer":
        query = (
            select(Payment)
            .join(Order, Order.id == Payment.order_id)
            .where(Order.user_id == user.id)
        )

    else:
        raise HTTPException(403, "Access denied")

    return db.scalars(query).all()


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    payment = db.get(Payment, payment_id)

    if not payment:
        raise HTTPException(404, "Payment not found")

    order = db.get(Order, payment.order_id)

    if user.role != "admin" and order.user_id != user.id:
        raise HTTPException(403, "Access denied")

    return payment


@router.patch("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int,
    data: PaymentUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(allow_roles("admin"))
):
    payment = db.scalar(
        select(Payment)
        .where(Payment.id == payment_id)
        .with_for_update()
    )

    if not payment:
        raise HTTPException(404, "Payment not found")

    if data.payment_status not in ["success", "failed"]:
        raise HTTPException(400, "Invalid payment status")

    if payment.payment_status != "pending":
        raise HTTPException(400, "Payment already processed")

    order = db.get(Order, payment.order_id)

    if order.order_status == "cancelled":
        raise HTTPException(400, "Order is cancelled")

    if data.payment_status == "success":
        cancellation = db.scalar(
            select(Cancellation).where(
                Cancellation.order_id == order.id,
                Cancellation.cancellation_status == "pending"
            )
        )

        if cancellation:
            raise HTTPException(409, "Cancellation request is pending")

    payment.payment_status = data.payment_status

    db.commit()
    db.refresh(payment)

    return payment
