
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.connection import get_db
from models.category_model import Category
from schema.category_schema import (
    CategoryCreate, CategoryUpdate, CategoryResponse
)
from utils.dependencies import allow_roles

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    admin=Depends(allow_roles("admin"))
):
    existing = db.scalar(
        select(Category).where(Category.name == data.name)
    )

    if existing:
        raise HTTPException(409, "Category already exists")

    category = Category(**data.model_dump())

    db.add(category)

    try:
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Category already exists")

    return category


@router.get("/", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category)).all()


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    category = db.get(Category, category_id)

    if not category:
        raise HTTPException(404, "Category not found")

    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def replace_category(
    category_id: int,
    data: CategoryCreate,
    db: Session = Depends(get_db),
    admin=Depends(allow_roles("admin"))
):
    category = db.get(Category, category_id)

    if not category:
        raise HTTPException(404, "Category not found")

    for key, value in data.model_dump().items():
        setattr(category, key, value)

    try:
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Category name already exists")

    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    admin=Depends(allow_roles("admin"))
):
    category = db.get(Category, category_id)

    if not category:
        raise HTTPException(404, "Category not found")

    updates = data.model_dump(exclude_unset=True)

    if updates.get("name", "valid") is None:
        raise HTTPException(422, "Category name cannot be null")

    for key, value in updates.items():
        setattr(category, key, value)

    try:
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Category name already exists")

    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin=Depends(allow_roles("admin"))
):
    from models.product_model import Product

    category = db.get(Category, category_id)

    if not category:
        raise HTTPException(404, "Category not found")

    product = db.scalar(
        select(Product.id).where(Product.category_id == category_id)
    )

    if product is not None:
        raise HTTPException(409, "Category contains products")

    db.delete(category)
    db.commit()
