"""
api/v1/conversations.py

Conversation management endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import get_current_user
from core.config import settings
from schemas.conversations import ConversationCreateRequest, ConversationResponse
from schemas.response import SuccessResponse, success
from services.conversation import ConversationService, get_conversation_service

router = APIRouter()
ConversationServiceDep = Annotated[
    ConversationService, Depends(get_conversation_service)
]
CurrentUserDep = Annotated[object, Depends(get_current_user)]


@router.post(
    "",
    response_model=SuccessResponse[ConversationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: CurrentUserDep,
    conversation_service: ConversationServiceDep,
) -> SuccessResponse[ConversationResponse]:
    return success(
        message="Conversation created successfully.",
        data=await conversation_service.create_conversation(request),
        version=settings.app_version,
    )


@router.get(
    "/{conversation_id}",
    response_model=SuccessResponse[ConversationResponse],
    status_code=status.HTTP_200_OK,
)
async def get_conversation(
    conversation_id: str,
    conversation_service: ConversationServiceDep,
) -> SuccessResponse[ConversationResponse]:
    result = await conversation_service.get_conversation(conversation_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found."
        )
    return success(
        message="Conversation retrieved.",
        data=result,
        version=settings.app_version,
    )


@router.get(
    "/project/{project_id}",
    response_model=SuccessResponse[list[ConversationResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_conversations(
    project_id: str,
    conversation_service: ConversationServiceDep,
) -> SuccessResponse[list[ConversationResponse]]:
    return success(
        message="Conversations retrieved.",
        data=await conversation_service.list_conversations(project_id),
        version=settings.app_version,
    )
