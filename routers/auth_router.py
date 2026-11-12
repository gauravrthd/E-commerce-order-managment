
import hashlib
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from jwt.exceptions import InvalidTokenError

from database.connection import get_db
from models.user_model import User
from models.auth_session_model import AuthSession
from schema.auth_schema import (
    RegisterRequest,
    TokenResponse,
    RefreshRequest,
    MessageResponse,
    UserResponse
)
from utils.password import hash_password, verify_password
from utils.security import create_token, decode_token
from utils.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_token_hash(jti: str):
    return hashlib.sha256(jti.encode()).hexdigest()


def invalid_token():
    return HTTPException(
        status_code=401,
        detail="Invalid credentials or token",
        headers={"WWW-Authenticate": "Bearer"}
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    email = str(data.email).lower()

    existing = db.scalar(
        select(User).where(User.email == email)
    )

    if existing:
        raise HTTPException(409, "Email already registered")

    user = User(
        name=data.name,
        email=email,
        mobile=data.mobile,
        role="customer",
        hashed_password=hash_password(data.password)
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already registered")

    return user


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form.username.strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(
        form.password, user.hashed_password
    ):
        raise invalid_token()

    session_id = str(uuid4())

    access_token, _, _ = create_token(
        user.id, session_id, "access"
    )

    refresh_token, jti, expires = create_token(
        user.id, session_id, "refresh"
    )

    session = AuthSession(
        id=session_id,
        user_id=user.id,
        refresh_jti_hash=get_token_hash(jti),
        refresh_expires_at=expires,
        revoked=False
    )

    db.add(session)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    data: RefreshRequest,
    db: Session = Depends(get_db)
):
    try:
        payload = decode_token(data.refresh_token, "refresh")
        user_id = int(payload["sub"])
        session_id = payload["sid"]
        token_hash = get_token_hash(payload["jti"])

    except (InvalidTokenError, ValueError, TypeError, KeyError):
        raise invalid_token()

    session = db.scalar(
        select(AuthSession)
        .where(AuthSession.id == session_id)
        .with_for_update()
    )

    if not session or session.revoked or session.user_id != user_id:
        raise invalid_token()

    if session.refresh_expires_at <= datetime.now(timezone.utc):
        raise invalid_token()

    if session.refresh_jti_hash != token_hash:
        session.revoked = True
        db.commit()
        raise invalid_token()

    user = db.get(User, user_id)

    if not user:
        raise invalid_token()

    access_token, _, _ = create_token(
        user.id, session_id, "access"
    )

    refresh_token, new_jti, expires = create_token(
        user.id, session_id, "refresh"
    )

    session.refresh_jti_hash = get_token_hash(new_jti)
    session.refresh_expires_at = expires

    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout", response_model=MessageResponse)
def logout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.scalars(
        select(AuthSession).where(
            AuthSession.user_id == user.id,
            AuthSession.revoked.is_(False)
        )
    ).all()

    for session in sessions:
        session.revoked = True

    db.commit()

    return {"message": "Logged out from all sessions successfully"}


@router.get("/me", response_model=UserResponse)
def get_profile(user: User = Depends(get_current_user)):
    return user
