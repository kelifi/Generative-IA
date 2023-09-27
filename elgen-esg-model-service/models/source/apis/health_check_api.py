from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from configuration.injection_container import DependencyContainer
from source.exceptions.api_exception_handler import ModelLoadAPIException
from source.services.model_service import LLMFactoryHuggingFace

health_check_router = APIRouter(prefix="/healthz")


@health_check_router.post('/')
@inject
def health_check(model: LLMFactoryHuggingFace = Depends(
    Provide[DependencyContainer.model])) -> JSONResponse:
    """
    Health check endpoint.
    Returns: Model status
    """
    if model.is_loaded_correctly():
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})

    raise ModelLoadAPIException(
        detail="The model is not loaded correctly.",
    )
