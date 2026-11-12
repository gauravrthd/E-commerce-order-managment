from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jwt.exceptions import InvalidTokenError

from database.connection import get_db
from models.user_model import User
from models.auth_session_model import AuthSession
from utils.security import decode_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = decode_token(token, "access")
        user_id = int(payload["sub"])
        session_id = payload["sid"]

    except (InvalidTokenError, ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    auth_session = db.get(AuthSession, session_id)

    if (
        not auth_session
        or auth_session.revoked
        or auth_session.user_id != user_id
    ):
        raise HTTPException(
            status_code=401,
            detail="Session expired or revoked"
        )

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


def allow_roles(*roles):

    def check_role(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )

        return user

    return check_role


def check_owner_or_admin(user: User, owner_id: int):
    if user.role != "admin" and user.id != owner_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )