from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import insert, select

from src.config import Settings
from src.db import SessionDep
from src.helper import credentials_exception, hash_password, verify_password
from src.models import User
from src.schemas import TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead)
def register(user: UserCreate, session: SessionDep):
    with session.begin():
        # Check user's exist
        stmt = select(User).where(User.username == user.username)
        res = session.exec(stmt).first()
        if res:
            _ = hash_password(user.password)

            raise HTTPException(status.HTTP_409_CONFLICT, detail="Registration failed.")

        # Create a user
        hashed_password = hash_password(user.password)
        stmt = (
            insert(User)
            .values(
                {
                    "username": user.username,
                    "hashed_password": hashed_password,
                    "role": user.role,
                }
            )
            .returning(User.id, User.username, User.role)
        )
        new_user = session.exec(stmt).first()

    return UserRead(id=new_user.id, username=new_user.username, role=new_user.role)


@router.post("/login", response_model=TokenResponse)
def login(
    user_form: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
):
    with session.begin():
        # Check user exist
        stmt = select(User).where(User.username == user_form.username)
        user = session.exec(stmt).first()
        if not user:
            _ = verify_password(user_form.password, "asdf")
            raise credentials_exception

        # Check password
        same_password = verify_password(user_form.password, user.hashed_password)
        if not same_password:
            raise credentials_exception

        # Create JWT
        settings = Settings()

        to_encode = user.model_dump()
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.jwt_algorithm
        )

        return TokenResponse(access_token=encoded_jwt, token_type="bearer")
