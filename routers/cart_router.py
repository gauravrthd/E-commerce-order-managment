
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.connection import get_db
from models.cart_model import Cart
from models.product_model import Product
from models.user_model import User
from schema.cart_schema import CartCreate, CartUpdate, CartResponse
from utils.dependencies import allow_roles

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.post("/", response_model=CartResponse, status_code=201)
def add_to_cart(
    data: CartCreate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("customer"))
):
    if data.user_id != user.id:
        raise HTTPException(403, "Access denied")

    product = db.get(Product, data.product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    if data.quantity > product.stock:
        raise HTTPException(400, "Insufficient stock")

    existing = db.scalar(
        select(Cart).where(
            Cart.user_id == user.id,
            Cart.product_id == data.product_id
        )
    )

    if existing:
        raise HTTPException(409, "Product already in cart")

    cart = Cart(
        user_id=user.id,
        product_id=data.product_id,
        quantity=data.quantity
    )

    db.add(cart)

    try:
        db.commit()
        db.refresh(cart)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Product already in cart")

    return cart


@router.get("/", response_model=list[CartResponse])
def get_cart(
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("customer"))
):
    return db.scalars(
        select(Cart).where(Cart.user_id == user.id)
    ).all()


@router.get("/{cart_id}", response_model=CartResponse)
def get_cart_item(
    cart_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("customer"))
):
    cart = db.get(Cart, cart_id)

    if not cart:
        raise HTTPException(404, "Cart item not found")

    if cart.user_id != user.id:
        raise HTTPException(403, "Access denied")

    return cart


@router.patch("/{cart_id}", response_model=CartResponse)
def update_cart(
    cart_id: int,
    data: CartUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("customer"))
):
    cart = db.get(Cart, cart_id)

    if not cart:
        raise HTTPException(404, "Cart item not found")

    if cart.user_id != user.id:
        raise HTTPException(403, "Access denied")

    updates = data.model_dump(exclude_unset=True)

    if not updates or updates.get("quantity") is None:
        raise HTTPException(400, "Quantity is required")

    if updates["quantity"] <= 0:
        raise HTTPException(400, "Invalid quantity")

    product = db.get(Product, cart.product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    if updates["quantity"] > product.stock:
        raise HTTPException(400, "Insufficient stock")

    cart.quantity = updates["quantity"]

    db.commit()
    db.refresh(cart)

    return cart


@router.delete("/{cart_id}", status_code=204)
def remove_from_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("customer"))
):
    cart = db.get(Cart, cart_id)

    if not cart:
        raise HTTPException(404, "Cart item not found")

    if cart.user_id != user.id:
        raise HTTPException(403, "Access denied")

    db.delete(cart)
    db.commit()
