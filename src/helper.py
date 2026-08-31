from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from src.config import Settings


def utc_now():
    return datetime.now(UTC)


password_hash = PasswordHash.recommended()


def hash_password(plain: str) -> str:
    hashed = password_hash.hash(plain)
    return hashed


def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid username or password.",
    headers={"WWW-Authenticate": "Bearer"},
)
