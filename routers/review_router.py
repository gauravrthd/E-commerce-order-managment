
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.connection import get_db
from models.user_model import User
from models.product_model import Product
from models.order_model import Order
from models.order_item_model import OrderItem
from models.review_model import Review
from schema.review_schema import (
    ReviewCreate, ReviewUpdate, ReviewResponse
)
from utils.dependencies import allow_roles

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=201)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("customer"))
):
    if data.user_id != user.id:
        raise HTTPException(403, "Access denied")

    if not db.get(Product, data.product_id):
        raise HTTPException(404, "Product not found")

    purchased = db.scalar(
        select(OrderItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.user_id == user.id,
            Order.order_status == "delivered",
            OrderItem.product_id == data.product_id
        )
    )

    if purchased is None:
        raise HTTPException(403, "Product not delivered yet")

    existing = db.scalar(
        select(Review).where(
            Review.user_id == user.id,
            Review.product_id == data.product_id
        )
    )

    if existing:
        raise HTTPException(409, "Review already exists")

    review = Review(
        user_id=user.id,
        product_id=data.product_id,
        rating=data.rating,
        comment=data.comment
    )

    db.add(review)

    try:
        db.commit()
        db.refresh(review)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Review already exists")

    return review


@router.get("/", response_model=list[ReviewResponse])
def get_reviews(db: Session = Depends(get_db)):
    return db.scalars(select(Review)).all()


@router.get("/product/{product_id}", response_model=list[ReviewResponse])
def get_product_reviews(
    product_id: int,
    db: Session = Depends(get_db)
):
    if not db.get(Product, product_id):
        raise HTTPException(404, "Product not found")

    return db.scalars(
        select(Review).where(Review.product_id == product_id)
    ).all()


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    review = db.get(Review, review_id)

    if not review:
        raise HTTPException(404, "Review not found")

    return review


@router.patch("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    data: ReviewUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("customer"))
):
    review = db.get(Review, review_id)

    if not review:
        raise HTTPException(404, "Review not found")

    if review.user_id != user.id:
        raise HTTPException(403, "Access denied")

    updates = data.model_dump(exclude_unset=True)

    if "rating" in updates and updates["rating"] is None:
        raise HTTPException(422, "Rating cannot be null")

    for key, value in updates.items():
        setattr(review, key, value)

    db.commit()
    db.refresh(review)

    return review


@router.delete("/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("customer", "admin"))
):
    review = db.get(Review, review_id)

    if not review:
        raise HTTPException(404, "Review not found")

    if user.role != "admin" and review.user_id != user.id:
        raise HTTPException(403, "Access denied")

    db.delete(review)
    db.commit()
