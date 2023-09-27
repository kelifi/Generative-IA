from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from sqlalchemy.exc import NoResultFound

from configuration.injection_container import DependencyContainer
from source.exceptions.service_exceptions import ModelCreationError, \
    ModelUpdateError, ModelRetrievalError
from source.exceptions.validation_exceptions import GenericValidationError
from source.schemas.models_schema import ModelOutputSchema, ModelInputSchema, ModelSourcesUpdateSchema
from source.services.model_service import ModelService

model_router = APIRouter(prefix="/models")


@model_router.get(path="", description="Get the available models from the ELGEN database",
                  response_model=list[ModelOutputSchema], summary="Get the list of available models for chat")
@inject
def get_available_models_for_chat(model_service: ModelService = Depends(Provide[DependencyContainer.model_service])):
    try:
        return model_service.get_models()
    except (GenericValidationError, ModelRetrievalError) as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error.message)


@model_router.get(path="/{model_code}", description="Get the model's source config from the ELGEN database per model code",
                  response_model=ModelSourcesUpdateSchema, summary="Get model's source config")
@inject
def get_model_per_code(model_service: ModelService = Depends(Provide[DependencyContainer.model_service]),
                       model_code: str = Path(description="the model's code")):
    try:
        return model_service.get_model_info_per_model_code(model_code=model_code)
    except (GenericValidationError, ModelRetrievalError) as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error.message)


@model_router.post(path="", description="Create a new model in the ELGEN database",
                   response_model=ModelOutputSchema, summary="add a new model with a unique model code")
@inject
def add_new_model(model_input: ModelInputSchema = Body(),
                  model_service: ModelService = Depends(Provide[DependencyContainer.model_service])):
    try:
        return model_service.add_model(model_input=model_input)
    except (GenericValidationError, ModelCreationError) as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error.message)


@model_router.patch(path="", description="Get the available models from the ELGEN database",
                    response_model=ModelOutputSchema, summary="Get the list of available models for chat")
@inject
def patch_model(model_sources_config: ModelSourcesUpdateSchema = Body(),
                model_service: ModelService = Depends(Provide[DependencyContainer.model_service])):
    try:
        return model_service.patch_model_configuration(model_sources_config=model_sources_config)
    except (GenericValidationError, ModelUpdateError) as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error.message)

    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No model exists with code {model_sources_config.code}")
