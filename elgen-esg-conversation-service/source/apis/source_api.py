from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Body, Path, status
from pydantic import ValidationError

from configuration.injection_container import DependencyContainer
from configuration.logging_setup import logger
from source.exceptions.api_exception_handler import ElgenAPIException
from source.exceptions.service_exceptions import SourceTypeFetchDataError, WorkspaceTypeNotFound, SourceAddingError, \
    SourceUpdatingError, SourceDataFetchError
from source.exceptions.validation_exceptions import GenericValidationError
from source.schemas.source_schema import SourceTypeOutputModel, NewSourceOutput, NewSourceSchema, SourceTypeModel
from source.services.source_service import SourceService

sources_router = APIRouter(prefix="/sources")


@sources_router.get(path="/type")
@inject
def get_available_sources_per_type(
        type_id: UUID = Query(..., description="Type of source"),
        source_service: SourceService = Depends(
            Provide[DependencyContainer.source_service])
) -> SourceTypeOutputModel:
    try:
        return source_service.get_available_sources_by_type(type_id)
    except SourceTypeFetchDataError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Cannot fetch types of sources !") from error
    except WorkspaceTypeNotFound as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error.message) from error


@sources_router.get(path="/type/{source_type_id}")
@inject
def get_source_type_by_id(
        source_type_id: UUID = Path(..., description="Id of Type source"),
        source_service: SourceService = Depends(
            Provide[DependencyContainer.source_service])
) -> SourceTypeModel:
    try:
        return source_service.get_source_type_by_id(source_type_id)
    except (GenericValidationError, SourceTypeFetchDataError) as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message)


@sources_router.post(path="", response_model=NewSourceOutput)
@inject
async def add_source(
        source: NewSourceSchema = Body(...),
        source_service: SourceService = Depends(
            Provide[DependencyContainer.source_service])
):
    try:
        return await source_service.add_source(source)
    except SourceAddingError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message)
    except ValidationError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="error getting infos of the added source")


@sources_router.patch(path="", response_model=NewSourceOutput)
@inject
async def update_source(
        source: NewSourceOutput = Body(...),
        source_service: SourceService = Depends(
            Provide[DependencyContainer.source_service])
):
    try:
        return await source_service.update_source(source)
    except SourceUpdatingError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message)
    except ValidationError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="error getting infos of the updated source")


@sources_router.get(path="/{source_id}", response_model=NewSourceOutput)
@inject
async def get_source_by_id(
        source_id: UUID = Path(),
        source_service: SourceService = Depends(Provide[DependencyContainer.source_service])
):
    try:
        return await source_service.get_source_by_id(source_id=source_id)
    except (SourceDataFetchError, GenericValidationError) as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="error occurs when getting source")


@sources_router.get(path="/workspace/{workspace_id}", response_model=NewSourceOutput)
@inject
async def get_source_by_workspace_id(
        workspace_id: UUID = Path(),
        source_service: SourceService = Depends(Provide[DependencyContainer.source_service])
):
    try:
        return await source_service.get_source_by_workspace_id(workspace_id=workspace_id)
    except SourceDataFetchError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Cannot get source")
