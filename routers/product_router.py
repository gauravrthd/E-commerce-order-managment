
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from schema.product_schema import (
    ProductCreate, ProductUpdate, ProductResponse
)
from utils.store import db, next_id
from utils.dependencies import allow_roles, get_current_user

router = APIRouter(prefix="/products", tags=["Products"])


def check_seller(product, user):
    if user["role"] == "admin":
        return

    if product["seller_id"] != user["id"]:
        raise HTTPException(403, "You can manage only your products")


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    product: ProductCreate,
    user=Depends(allow_roles("shopkeeper", "admin"))
):
    if product.category_id not in db["categories"]:
        raise HTTPException(404, "Category not found")

    seller = db["users"].get(product.seller_id)

    if not seller or seller["role"] != "shopkeeper":
        raise HTTPException(400, "Invalid shopkeeper ID")

    if user["role"] == "shopkeeper" and product.seller_id != user["id"]:
        raise HTTPException(403, "Cannot create products for other sellers")

    product_id = next_id("products")

    data = product.model_dump()
    data["id"] = product_id

    db["products"][product_id] = data
    return data


@router.get("/", response_model=list[ProductResponse])
def get_products(
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
):
    products = list(db["products"].values())

    if category_id is not None:
        products = [
            p for p in products if p["category_id"] == category_id
        ]

    if min_price is not None:
        products = [
            p for p in products if p["price"] >= min_price
        ]

    if max_price is not None:
        products = [
            p for p in products if p["price"] <= max_price
        ]

    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    product = db["products"].get(product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    return product


@router.put("/{product_id}", response_model=ProductResponse)
def replace_product(
    product_id: int,
    data: ProductCreate,
    user=Depends(allow_roles("shopkeeper", "admin"))
):
    old = db["products"].get(product_id)

    if not old:
        raise HTTPException(404, "Product not found")

    check_seller(old, user)

    if data.category_id not in db["categories"]:
        raise HTTPException(404, "Category not found")

    if data.seller_id != old["seller_id"]:
        raise HTTPException(400, "Cannot change the product seller")

    updated = {"id": product_id, **data.model_dump()}
    db["products"][product_id] = updated

    return updated


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    user=Depends(allow_roles("shopkeeper", "admin"))
):
    product = db["products"].get(product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    check_seller(product, user)

    updates = data.model_dump(exclude_unset=True)

    if "category_id" in updates:
        if updates["category_id"] not in db["categories"]:
            raise HTTPException(404, "Category not found")

    product.update(updates)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    user=Depends(allow_roles("shopkeeper", "admin"))
):
    product = db["products"].get(product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    check_seller(product, user)

    if any(
        item["product_id"] == product_id
        for item in db["order_items"].values()
    ):
        raise HTTPException(
            409, "Product has order history and cannot be deleted"
        )

    for cart_id, item in list(db["cart"].items()):
        if item["product_id"] == product_id:
            del db["cart"][cart_id]

    del db["products"][product_id]
