
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.connection import get_db
from models.user_model import User
from schema.user_schema import UserCreate, UserUpdate, UserResponse
from utils.password import hash_password
from utils.dependencies import get_current_user, allow_roles

from celery_app.email_tasks import send_welcome_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


class RoleUpdate(BaseModel):
    role: str


def queue_welcome_email(user: User):
    try:
        send_welcome_email.delay(
            user.email,
            user.name
        )
        logger.info(
            "Welcome email queued for user_id=%s",
            user.id
        )
    except Exception:
        logger.exception(
            "Failed to queue welcome email for user_id=%s",
            user.id
        )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    email = str(user.email).strip().lower()

    existing = db.scalar(
        select(User).where(User.email == email)
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    new_user = User(
        name=user.name,
        email=email,
        mobile=user.mobile,
        role="customer",
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    queue_welcome_email(new_user)

    return new_user


@router.post(
    "/shopkeepers",
    response_model=UserResponse,
    status_code=201
)
def create_shopkeeper(
    user: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(allow_roles("admin"))
):
    email = str(user.email).strip().lower()

    existing = db.scalar(
        select(User).where(User.email == email)
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    new_user = User(
        name=user.name,
        email=email,
        mobile=user.mobile,
        role="shopkeeper",
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    queue_welcome_email(new_user)

    return new_user


@router.get(
    "/",
    response_model=list[UserResponse]
)
def get_users(
    db: Session = Depends(get_db),
    admin: User = Depends(allow_roles("admin"))
):
    return db.scalars(
        select(User)
    ).all()


@router.get(
    "/me",
    response_model=UserResponse
)
def my_profile(
    user: User = Depends(get_current_user)
):
    return user


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    if current.role != "admin" and current.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse
)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    if current.role != "admin" and current.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    updates = data.model_dump(exclude_unset=True)

    if any(value is None for value in updates.values()):
        raise HTTPException(
            status_code=422,
            detail="Fields cannot be null"
        )

    if "email" in updates:
        updates["email"] = str(
            updates["email"]
        ).strip().lower()

    for key, value in updates.items():
        setattr(user, key, value)

    try:
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    return user


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse
)
def change_role(
    user_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(allow_roles("admin"))
):
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if data.role not in [
        "customer",
        "shopkeeper",
        "admin"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    if user.id == admin.id and data.role != "admin":
        raise HTTPException(
            status_code=400,
            detail="Cannot remove your own admin role"
        )

    if user.role != data.role:
        user.role = data.role

        db.commit()
        db.refresh(user)

    return user
