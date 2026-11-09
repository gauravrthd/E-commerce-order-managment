
from fastapi import APIRouter, Depends, HTTPException

from schema.cart_schema import (
    CartCreate, CartUpdate, CartResponse
)
from utils.store import db, next_id
from utils.dependencies import allow_roles

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.post("/", response_model=CartResponse, status_code=201)
def add_to_cart(
    cart: CartCreate,
    user=Depends(allow_roles("customer"))
):
    if cart.user_id != user["id"]:
        raise HTTPException(403, "Cannot add items to another user's cart")

    product = db["products"].get(cart.product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    existing = next(
        (
            item for item in db["cart"].values()
            if item["user_id"] == user["id"]
            and item["product_id"] == cart.product_id
        ),
        None
    )

    if existing:
        raise HTTPException(409, "Product already exists in cart")

    if cart.quantity > product["stock"]:
        raise HTTPException(400, "Insufficient stock")

    cart_id = next_id("cart")
    data = cart.model_dump()
    data["id"] = cart_id

    db["cart"][cart_id] = data
    return data


@router.get("/", response_model=list[CartResponse])
def get_my_cart(user=Depends(allow_roles("customer"))):
    return [
        item for item in db["cart"].values()
        if item["user_id"] == user["id"]
    ]


@router.patch("/{cart_id}", response_model=CartResponse)
def update_cart(
    cart_id: int,
    data: CartUpdate,
    user=Depends(allow_roles("customer"))
):
    cart = db["cart"].get(cart_id)

    if not cart:
        raise HTTPException(404, "Cart item not found")

    if cart["user_id"] != user["id"]:
        raise HTTPException(403, "Access denied")

    updates = data.model_dump(exclude_unset=True)

    quantity = updates.get("quantity", cart["quantity"])
    product = db["products"].get(cart["product_id"])

    if not product:
        raise HTTPException(404, "Product not found")

    if quantity > product["stock"]:
        raise HTTPException(400, "Insufficient stock")

    cart.update(updates)
    return cart


@router.delete("/{cart_id}", status_code=204)
def remove_from_cart(
    cart_id: int,
    user=Depends(allow_roles("customer"))
):
    cart = db["cart"].get(cart_id)

    if not cart:
        raise HTTPException(404, "Cart item not found")

    if cart["user_id"] != user["id"]:
        raise HTTPException(403, "Access denied")

    del db["cart"][cart_id]
