"""
services/auth.py

Authentication use cases, user registration, and token generation.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import create_access_token, get_password_hash, verify_password
from database.session import get_db_session
from models.user import User
from repositories.user import UserRepository
from schemas.auth import (
    AuthTokenResponse,
    UserLoginRequest,
    UserProfile,
    UserRegisterRequest,
)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    async def register(self, request: UserRegisterRequest) -> UserProfile:
        existing = await self._repo.get_by_email(request.email)
        if existing:
            raise ValueError("Email already registered.")

        user = User(
            email=request.email,
            hashed_password=get_password_hash(request.password),
            full_name=request.full_name,
            is_active=True,
        )
        user = await self._repo.create(user)
        return UserProfile.model_validate(user)

    async def login(self, request: UserLoginRequest) -> AuthTokenResponse:
        user = await self._repo.get_by_email(request.email)
        if user is None or not verify_password(request.password, user.hashed_password):
            raise ValueError("Invalid email or password.")

        token = create_access_token({"sub": str(user.id)})
        return AuthTokenResponse(access_token=token)

    async def get_profile(self, user_id: int) -> UserProfile | None:
        user = await self._repo.get_by_id(user_id)
        return UserProfile.model_validate(user) if user else None


def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuthService:
    return AuthService(session)
