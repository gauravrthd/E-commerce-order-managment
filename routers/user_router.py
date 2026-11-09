
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from schema.user_schema import (
    UserCreate, UserUpdate, UserResponse
)
from utils.store import db, next_id
from utils.password import hash_password
from utils.dependencies import (
    get_current_user, allow_roles, check_owner_or_admin
)

router = APIRouter(prefix="/users", tags=["Users"])


class RoleUpdate(BaseModel):
    role: str


def create_user_record(user, role):
    if any(
        u["email"] == user.email
        for u in db["users"].values()
    ):
        raise HTTPException(409, "Email already registered")

    user_id = next_id("users")

    data = user.model_dump(exclude={"password"})
    data["id"] = user_id
    data["role"] = role
    data["hashed_password"] = hash_password(user.password)

    db["users"][user_id] = data
    return data


@router.post("/register", response_model=UserResponse, status_code=201)
def register_customer(user: UserCreate):
    return create_user_record(user, "customer")


@router.post("/shopkeepers", response_model=UserResponse, status_code=201)
def create_shopkeeper(
    user: UserCreate,
    admin=Depends(allow_roles("admin"))
):
    return create_user_record(user, "shopkeeper")


@router.get("/", response_model=list[UserResponse])
def get_users(admin=Depends(allow_roles("admin"))):
    return list(db["users"].values())


@router.get("/me", response_model=UserResponse)
def get_my_profile(user=Depends(get_current_user)):
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current=Depends(get_current_user)):
    check_owner_or_admin(current, user_id)

    user = db["users"].get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    current=Depends(get_current_user)
):
    check_owner_or_admin(current, user_id)

    user = db["users"].get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    updates = data.model_dump(exclude_unset=True)

    if "email" in updates:
        if any(
            u["email"] == updates["email"] and u["id"] != user_id
            for u in db["users"].values()
        ):
            raise HTTPException(409, "Email already registered")

    user.update(updates)
    return user


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_role(
    user_id: int,
    data: RoleUpdate,
    admin=Depends(allow_roles("admin"))
):
    user = db["users"].get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if data.role not in ["customer", "shopkeeper", "admin"]:
        raise HTTPException(400, "Invalid role")

    user["role"] = data.role
    return user
