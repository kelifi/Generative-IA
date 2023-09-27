from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Body, status
from pydantic import ValidationError

from configuration.injection_container import DependencyContainer
from source.exceptions.api_exception_handler import ElgenAPIException
from source.exceptions.model_exception_handler import ModelError, PromptError
from source.schemas.api_schemas import PromptInputSchema
from source.schemas.model_answer_schema import ModelAnswer
from source.services.model_service import LLMFactoryHuggingFace

router = APIRouter(prefix="/inference")


@router.post('/old', deprecated=True)
@inject
def chat_inference(
        model: LLMFactoryHuggingFace = Depends(
            Provide[DependencyContainer.model]),
        prompt: str = Body(...)):
    """

    :param preprocessing_method:
    :param model_inference_context:
    :param prompt: The PROMPT to be sent to the text generation model
    :return:
    """
    try:
        return model.predict(prompt)
    except ModelError as model_prediction_error:
        raise ElgenAPIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to generate answer : {model_prediction_error}'
        )


@router.post('')
@inject
def inference_benchmark(
        model: LLMFactoryHuggingFace = Depends(
            Provide[DependencyContainer.model]),
        input_prompt: PromptInputSchema = Body(...)) -> ModelAnswer:
    """
    Generate an answer from the model with benchmark statistics
     (prompt length and the time the model takes to generate the complete answer to the provided prompt)
    Args:
        model:  
        input_prompt: Prompt to be fed to the LLM.

    Returns:
        The model answer for the given prompt.
    """

    try:
        return model.generate_answer(input_prompt.prompt)
    except PromptError as error:
        raise ElgenAPIException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                detail=error.detail)
    except (ModelError, ValidationError) as error:
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to generate model answer: {error}")
