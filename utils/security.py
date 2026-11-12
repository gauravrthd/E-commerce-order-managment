import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = "HS256"

ACCESS_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def create_token(user_id: int, session_id: str, token_type: str):
    now = datetime.now(timezone.utc)

    if token_type == "access":
        expires = now + timedelta(minutes=ACCESS_MINUTES)
    elif token_type == "refresh":
        expires = now + timedelta(days=REFRESH_DAYS)
    else:
        raise ValueError("Invalid token type")

    jti = str(uuid4())

    payload = {
        "sub": str(user_id),
        "sid": session_id,
        "jti": jti,
        "type": token_type,
        "iat": now,
        "exp": expires
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token, jti, expires


def decode_token(token: str, expected_type: str):
    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        options={
            "require": ["sub", "sid", "jti", "type", "iat", "exp"]
        }
    )

    if payload.get("type") != expected_type:
        raise InvalidTokenError("Invalid token type")

    return payload