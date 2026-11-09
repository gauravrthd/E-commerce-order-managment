
from fastapi import APIRouter, Depends, HTTPException

from schema.payment_schema import (
    PaymentCreate, PaymentUpdate, PaymentResponse
)
from utils.store import db, next_id
from utils.dependencies import get_current_user, allow_roles

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(
    payment: PaymentCreate,
    user=Depends(allow_roles("customer"))
):
    order = db["orders"].get(payment.order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    if order["user_id"] != user["id"]:
        raise HTTPException(403, "Access denied")

    if order["order_status"] == "cancelled":
        raise HTTPException(400, "Cannot pay for a cancelled order")

    if payment.payment_method not in ["upi", "card", "cod"]:
        raise HTTPException(400, "Invalid payment method")

    if any(
        p["order_id"] == payment.order_id
        for p in db["payments"].values()
    ):
        raise HTTPException(409, "Payment record already exists")

    payment_id = next_id("payments")

    data = {
        "id": payment_id,
        "order_id": payment.order_id,
        "amount": order["total_amount"],
        "payment_method": payment.payment_method,
        "payment_status": "pending"
    }

    db["payments"][payment_id] = data
    return data


@router.get("/", response_model=list[PaymentResponse])
def get_payments(user=Depends(get_current_user)):
    payments = list(db["payments"].values())

    if user["role"] == "admin":
        return payments

    if user["role"] == "customer":
        return [
            p for p in payments
            if db["orders"][p["order_id"]]["user_id"] == user["id"]
        ]

    raise HTTPException(403, "Access denied")


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    user=Depends(get_current_user)
):
    payment = db["payments"].get(payment_id)

    if not payment:
        raise HTTPException(404, "Payment not found")

    order = db["orders"][payment["order_id"]]

    if user["role"] != "admin" and order["user_id"] != user["id"]:
        raise HTTPException(403, "Access denied")

    return payment


@router.patch("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int,
    data: PaymentUpdate,
    admin=Depends(allow_roles("admin"))
):
    payment = db["payments"].get(payment_id)

    if not payment:
        raise HTTPException(404, "Payment not found")

    if data.payment_status not in ["success", "failed"]:
        raise HTTPException(400, "Invalid payment status")

    if payment["payment_status"] != "pending":
        raise HTTPException(400, "Payment already processed")

    order = db["orders"][payment["order_id"]]

    if order["order_status"] == "cancelled":
        raise HTTPException(409, "Order was cancelled")

    if data.payment_status == "success":
        cancellation_pending = any(
            c["order_id"] == order["id"]
            and c["cancellation_status"] == "pending"
            for c in db["cancellations"].values()
        )
        if cancellation_pending:
            raise HTTPException(
                409, "Resolve cancellation request first"
            )

    payment["payment_status"] = data.payment_status
    return payment
