
from fastapi import APIRouter, Depends, HTTPException

from schema.review_schema import (
    ReviewCreate, ReviewUpdate, ReviewResponse
)
from utils.store import db, next_id
from utils.dependencies import allow_roles, get_order_items

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=201)
def create_review(
    review: ReviewCreate,
    user=Depends(allow_roles("customer"))
):
    if review.user_id != user["id"]:
        raise HTTPException(403, "Cannot review for another user")

    if review.product_id not in db["products"]:
        raise HTTPException(404, "Product not found")

    purchased = any(
        order["user_id"] == user["id"]
        and order["order_status"] == "delivered"
        and any(
            item["product_id"] == review.product_id
            for item in get_order_items(order["id"])
        )
        for order in db["orders"].values()
    )

    if not purchased:
        raise HTTPException(
            403, "You can review only delivered products"
        )

    if any(
        r["user_id"] == user["id"]
        and r["product_id"] == review.product_id
        for r in db["reviews"].values()
    ):
        raise HTTPException(409, "You already reviewed this product")

    review_id = next_id("reviews")

    data = review.model_dump()
    data["id"] = review_id

    db["reviews"][review_id] = data
    return data


@router.get("/", response_model=list[ReviewResponse])
def get_reviews():
    return list(db["reviews"].values())


@router.get("/product/{product_id}", response_model=list[ReviewResponse])
def get_product_reviews(product_id: int):
    if product_id not in db["products"]:
        raise HTTPException(404, "Product not found")

    return [
        review for review in db["reviews"].values()
        if review["product_id"] == product_id
    ]


@router.patch("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    data: ReviewUpdate,
    user=Depends(allow_roles("customer"))
):
    review = db["reviews"].get(review_id)

    if not review:
        raise HTTPException(404, "Review not found")

    if review["user_id"] != user["id"]:
        raise HTTPException(403, "Access denied")

    review.update(data.model_dump(exclude_unset=True))
    return review


@router.delete("/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    user=Depends(allow_roles("customer", "admin"))
):
    review = db["reviews"].get(review_id)

    if not review:
        raise HTTPException(404, "Review not found")

    if user["role"] != "admin" and review["user_id"] != user["id"]:
        raise HTTPException(403, "Access denied")

    del db["reviews"][review_id]
