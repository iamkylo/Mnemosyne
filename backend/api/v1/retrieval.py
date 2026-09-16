"""
api/v1/retrieval.py

Semantic retrieval endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from core.auth import get_current_user
from core.config import settings
from schemas.retrieval import RetrievalRequest, RetrievalResult
from schemas.response import SuccessResponse, success
from services.search import RetrievalService, get_retrieval_service

router = APIRouter()
RetrievalServiceDep = Annotated[RetrievalService, Depends(get_retrieval_service)]
CurrentUserDep = Annotated[object, Depends(get_current_user)]


@router.post(
    "",
    response_model=SuccessResponse[RetrievalResult],
    status_code=status.HTTP_200_OK,
)
async def retrieve_context(
    request: RetrievalRequest,
    _: CurrentUserDep,
    retrieval_service: RetrievalServiceDep,
) -> SuccessResponse[RetrievalResult]:
    result = await retrieval_service.retrieve(request)
    return success(
        message="Semantic retrieval completed.",
        data=result,
        version=settings.app_version,
    )
