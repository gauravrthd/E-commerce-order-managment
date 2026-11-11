
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.connection import get_db
from models.product_model import Product
from models.category_model import Category
from models.user_model import User
from models.cart_model import Cart
from models.order_item_model import OrderItem
from schema.product_schema import (
    ProductCreate, ProductUpdate, ProductResponse
)
from utils.dependencies import allow_roles

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("shopkeeper", "admin"))
):
    if not db.get(Category, data.category_id):
        raise HTTPException(404, "Category not found")

    seller = db.get(User, data.seller_id)

    if not seller or seller.role != "shopkeeper":
        raise HTTPException(400, "Invalid shopkeeper")

    if user.role == "shopkeeper" and user.id != data.seller_id:
        raise HTTPException(403, "Cannot create another seller's product")

    product = Product(**data.model_dump())

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get("/", response_model=list[ProductResponse])
def get_products(
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    db: Session = Depends(get_db)
):
    query = select(Product)

    if category_id is not None:
        query = query.where(Product.category_id == category_id)

    if min_price is not None:
        query = query.where(Product.price >= min_price)

    if max_price is not None:
        query = query.where(Product.price <= max_price)

    return db.scalars(query).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    return product


@router.put("/{product_id}", response_model=ProductResponse)
def replace_product(
    product_id: int,
    data: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("shopkeeper", "admin"))
):
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    if user.role != "admin" and product.seller_id != user.id:
        raise HTTPException(403, "Access denied")

    if not db.get(Category, data.category_id):
        raise HTTPException(404, "Category not found")

    if data.seller_id != product.seller_id:
        raise HTTPException(400, "Cannot change product seller")

    for key, value in data.model_dump().items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("shopkeeper", "admin"))
):
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    if user.role != "admin" and product.seller_id != user.id:
        raise HTTPException(403, "Access denied")

    updates = data.model_dump(exclude_unset=True)

    if any(
        value is None and key != "description"
        for key, value in updates.items()
    ):
        raise HTTPException(422, "Invalid null value")

    if "category_id" in updates:
        if not db.get(Category, updates["category_id"]):
            raise HTTPException(404, "Category not found")

    for key, value in updates.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles("shopkeeper", "admin"))
):
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    if user.role != "admin" and product.seller_id != user.id:
        raise HTTPException(403, "Access denied")

    existing_order = db.scalar(
        select(OrderItem.id).where(OrderItem.product_id == product_id)
    )

    if existing_order is not None:
        raise HTTPException(409, "Product has order history")

    cart_items = db.scalars(
        select(Cart).where(Cart.product_id == product_id)
    ).all()

    for item in cart_items:
        db.delete(item)

    db.delete(product)
    db.commit()
