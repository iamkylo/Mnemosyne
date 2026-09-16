"""
core/auth.py

FastAPI dependency that validates the Bearer token on every protected endpoint
and returns the authenticated user.

Usage
-----
from core.auth import get_current_user

@router.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    ...
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decode_access_token
from database.session import get_db_session
from repositories.user import UserRepository
from schemas.auth import UserProfile

_bearer = HTTPBearer(auto_error=True)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserProfile:
    """
    FastAPI dependency — validate Bearer token and return the authenticated user.

    Raises HTTP 401 if the token is missing, malformed, expired, or the user
    no longer exists in the database.
    """
    try:
        payload = decode_access_token(credentials.credentials)
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise _CREDENTIALS_EXCEPTION
        user_id = int(user_id_raw)
    except (JWTError, ValueError):
        raise _CREDENTIALS_EXCEPTION

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXCEPTION

    return UserProfile.model_validate(user)
