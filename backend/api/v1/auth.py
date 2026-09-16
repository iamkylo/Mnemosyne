"""
api/v1/auth.py

Authentication endpoints for user registration and login.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from core.config import settings
from core.auth import get_current_user
from schemas.auth import (
    AuthTokenResponse,
    UserLoginRequest,
    UserProfile,
    UserRegisterRequest,
)
from schemas.response import SuccessResponse, success
from services.auth import AuthService, get_auth_service

router = APIRouter()
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[UserProfile, Depends(get_current_user)]


@router.post(
    "/register",
    response_model=SuccessResponse[UserProfile],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: UserRegisterRequest,
    auth_service: AuthServiceDep,
) -> SuccessResponse[UserProfile]:
    try:
        profile = await auth_service.register(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return success(
        message="User created successfully.",
        data=profile,
        version=settings.app_version,
    )


@router.post(
    "/login",
    response_model=SuccessResponse[AuthTokenResponse],
    status_code=status.HTTP_200_OK,
)
async def login(
    request: UserLoginRequest,
    auth_service: AuthServiceDep,
) -> SuccessResponse[AuthTokenResponse]:
    try:
        token = await auth_service.login(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return success(
        message="Authentication successful.",
        data=token,
        version=settings.app_version,
    )


@router.get(
    "/me",
    response_model=SuccessResponse[UserProfile],
    status_code=status.HTTP_200_OK,
)
async def me(current_user: CurrentUserDep) -> SuccessResponse[UserProfile]:
    return success(
        message="Authenticated user profile.",
        data=UserProfile.model_validate(current_user),
        version=settings.app_version,
    )
