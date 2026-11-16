
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
from models.review_model import Review

from schema.product_schema import (
    ProductCreate, ProductUpdate, ProductResponse
)
from utils.dependencies import allow_roles

from cache.redis_cache import (
    get_cached_products,
    set_cached_products,
    invalidate_product_cache
)

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

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Could not create product")

    invalidate_product_cache()

    return product


@router.get("/", response_model=list[ProductResponse])
def get_products(
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    db: Session = Depends(get_db)
):
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(400, "Invalid price range")

    filters = {
        "category_id": category_id,
        "min_price": min_price,
        "max_price": max_price
    }

    cached_products, cache_key = get_cached_products(filters)

    if cached_products is not None:
        return cached_products

    query = select(Product)

    if category_id is not None:
        query = query.where(Product.category_id == category_id)

    if min_price is not None:
        query = query.where(Product.price >= min_price)

    if max_price is not None:
        query = query.where(Product.price <= max_price)

    products = db.scalars(query).all()

    result = [
        ProductResponse.model_validate(
            product,
            from_attributes=True
        ).model_dump(mode="json")
        for product in products
    ]

    set_cached_products(cache_key, result)

    return result


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

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Could not update product")

    invalidate_product_cache()

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

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Could not update product")

    invalidate_product_cache()

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
        select(OrderItem.id).where(
            OrderItem.product_id == product_id
        )
    )

    if existing_order is not None:
        raise HTTPException(409, "Product has order history")

    existing_review = db.scalar(
        select(Review.id).where(
            Review.product_id == product_id
        )
    )

    if existing_review is not None:
        raise HTTPException(409, "Product has reviews")

    cart_items = db.scalars(
        select(Cart).where(Cart.product_id == product_id)
    ).all()

    for item in cart_items:
        db.delete(item)

    db.delete(product)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Product cannot be deleted")

    invalidate_product_cache()
