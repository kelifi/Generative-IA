from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Body, status
from pydantic import ValidationError

from configuration.injection_container import DependencyContainer
from source.exceptions.api_exception_handler import AnswerGenerationApiError
from source.exceptions.model_exception_handler import PredictionError
from source.schemas.api_schemas import PromptInputSchema
from source.schemas.model_answer_schema import ModelAnswer
from source.services.model_service import OpenAIService, logger

router = APIRouter(prefix="/inference")


@router.post('')
@inject
def generate_answer(
        model: OpenAIService = Depends(
            Provide[DependencyContainer.open_ai_model]),
        input_prompt: PromptInputSchema = Body(...)) -> ModelAnswer:
    """
    Generate an answer from one of the available online models
     
    Args:
        model: the llm
        input_prompt: Prompt to be fed to the LLM.

    Returns:
        The model answer for the given prompt.
    """
    try:
        return model.generate_answer(input_prompt.prompt)
    except (PredictionError, ValidationError) as error:
        logger.error(error)
        raise AnswerGenerationApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate model answer: {error}",
        ) from error
