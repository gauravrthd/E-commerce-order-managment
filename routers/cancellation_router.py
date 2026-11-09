
from fastapi import APIRouter, Depends, HTTPException

from schema.cancellation_schema import (
    CancellationCreate, CancellationUpdate,
    CancellationResponse
)
from utils.store import db, next_id
from utils.dependencies import (
    get_current_user, allow_roles, get_order_items
)

router = APIRouter(
    prefix="/cancellations",
    tags=["Order Cancellations"]
)


@router.post("/", response_model=CancellationResponse, status_code=201)
def request_cancellation(
    data: CancellationCreate,
    user=Depends(allow_roles("customer"))
):
    order = db["orders"].get(data.order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    if order["user_id"] != user["id"]:
        raise HTTPException(403, "Access denied")

    if order["order_status"] not in ["pending", "confirmed"]:
        raise HTTPException(400, "Order cannot be cancelled")

    if any(
        c["order_id"] == data.order_id
        for c in db["cancellations"].values()
    ):
        raise HTTPException(409, "Cancellation already requested")

    if any(
        p["order_id"] == data.order_id
        and p["payment_status"] == "success"
        for p in db["payments"].values()
    ):
        raise HTTPException(
            409, "Paid order needs refund handling before cancellation"
        )

    cancellation_id = next_id("cancellations")

    cancellation = {
        "id": cancellation_id,
        "order_id": data.order_id,
        "reason": data.reason,
        "cancellation_status": "pending"
    }

    db["cancellations"][cancellation_id] = cancellation
    return cancellation


@router.get("/", response_model=list[CancellationResponse])
def get_cancellations(user=Depends(get_current_user)):
    cancellations = list(db["cancellations"].values())

    if user["role"] == "admin":
        return cancellations

    if user["role"] == "customer":
        return [
            c for c in cancellations
            if db["orders"][c["order_id"]]["user_id"] == user["id"]
        ]

    raise HTTPException(403, "Access denied")


@router.patch(
    "/{cancellation_id}",
    response_model=CancellationResponse
)
def update_cancellation(
    cancellation_id: int,
    data: CancellationUpdate,
    admin=Depends(allow_roles("admin"))
):
    cancellation = db["cancellations"].get(cancellation_id)

    if not cancellation:
        raise HTTPException(404, "Cancellation not found")

    if cancellation["cancellation_status"] != "pending":
        raise HTTPException(400, "Cancellation already processed")

    if data.cancellation_status not in ["approved", "rejected"]:
        raise HTTPException(400, "Use approved or rejected")

    order = db["orders"][cancellation["order_id"]]

    if data.cancellation_status == "approved":
        if order["order_status"] not in ["pending", "confirmed"]:
            raise HTTPException(409, "Order can no longer be cancelled")

        if any(
            p["order_id"] == order["id"]
            and p["payment_status"] == "success"
            for p in db["payments"].values()
        ):
            raise HTTPException(409, "Refund handling required")

        for item in get_order_items(order["id"]):
            product = db["products"].get(item["product_id"])

            if product:
                product["stock"] += item["quantity"]

        order["order_status"] = "cancelled"

    cancellation["cancellation_status"] = data.cancellation_status
    return cancellation
