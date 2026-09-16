"""
api/v1/evaluation.py

Memory evaluation endpoint.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from core.auth import get_current_user
from core.config import settings
from memory_engine.evaluation.evaluator import MemoryEvaluator
from schemas.evaluation import EvaluationRequest, EvaluationResult
from schemas.response import SuccessResponse, success

router = APIRouter()
CurrentUserDep = Annotated[object, Depends(get_current_user)]


@router.post(
    "/evaluate",
    response_model=SuccessResponse[EvaluationResult],
    status_code=status.HTTP_200_OK,
    summary="Evaluate retrieved context quality",
)
async def evaluate_context(
    request: EvaluationRequest,
    _: CurrentUserDep,
) -> SuccessResponse[EvaluationResult]:
    """
    Analyse retrieved context and return precision, redundancy, and efficiency metrics.
    """
    evaluator = MemoryEvaluator()
    result = evaluator.evaluate(request)
    return success(
        message="Context evaluation completed.",
        data=result,
        version=settings.app_version,
    )
