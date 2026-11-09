
from fastapi import APIRouter, Depends, HTTPException

from schema.category_schema import (
    CategoryCreate, CategoryUpdate, CategoryResponse
)
from utils.store import db, next_id
from utils.dependencies import allow_roles

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(
    category: CategoryCreate,
    user=Depends(allow_roles("admin"))
):
    if any(
        c["name"].lower() == category.name.lower()
        for c in db["categories"].values()
    ):
        raise HTTPException(409, "Category already exists")

    category_id = next_id("categories")

    data = category.model_dump()
    data["id"] = category_id

    db["categories"][category_id] = data
    return data


@router.get("/", response_model=list[CategoryResponse])
def get_categories():
    return list(db["categories"].values())


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int):
    category = db["categories"].get(category_id)

    if not category:
        raise HTTPException(404, "Category not found")

    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def replace_category(
    category_id: int,
    data: CategoryCreate,
    user=Depends(allow_roles("admin"))
):
    if category_id not in db["categories"]:
        raise HTTPException(404, "Category not found")

    for category in db["categories"].values():
        if (
            category["id"] != category_id
            and category["name"].lower() == data.name.lower()
        ):
            raise HTTPException(409, "Category already exists")

    updated = {"id": category_id, **data.model_dump()}
    db["categories"][category_id] = updated
    return updated


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    user=Depends(allow_roles("admin"))
):
    category = db["categories"].get(category_id)

    if not category:
        raise HTTPException(404, "Category not found")

    updates = data.model_dump(exclude_unset=True)

    if "name" in updates and updates["name"] is not None:
        if any(
            c["id"] != category_id
            and c["name"].lower() == updates["name"].lower()
            for c in db["categories"].values()
        ):
            raise HTTPException(409, "Category already exists")

    category.update(updates)
    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    user=Depends(allow_roles("admin"))
):
    if category_id not in db["categories"]:
        raise HTTPException(404, "Category not found")

    if any(
        p["category_id"] == category_id
        for p in db["products"].values()
    ):
        raise HTTPException(409, "Category contains products")

    del db["categories"][category_id]
