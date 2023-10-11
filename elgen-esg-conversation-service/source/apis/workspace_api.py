from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, Path, Body
from fastapi import status
from pydantic import ValidationError

from configuration.injection_container import DependencyContainer
from configuration.logging_setup import logger
from source.exceptions.api_exception_handler import ElgenAPIException
from source.exceptions.service_exceptions import WorkspaceFetchDataError, WorkspaceCreationError, \
    WorkspaceTypeFetchDataError, WorkspaceTypeCreationError, SourceDataFetchError, SourceUpdatingError, \
    WorkspaceNotFoundError
from source.exceptions.validation_exceptions import GenericValidationError
from source.schemas.common import UpdateStatusDataModel
from source.schemas.workspace_schema import WorkspaceOutput, WorkspaceInput, \
    WorkspaceUsersApiModel, WorkspaceTypeInput, WorkspaceTypeOutputModel, WorkspaceTypeModel, \
    GenericWorkspaceInfoOutput
from source.services.source_service import SourceService
from source.services.workspace_service import WorkspaceService

workspace_router = APIRouter(prefix="/workspaces")


@workspace_router.get(path="/users", response_model=GenericWorkspaceInfoOutput)
@inject
def get_workspaces_by_user(
        user_id: UUID = Header(..., alias='user-id'),
        workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])
):
    try:
        return GenericWorkspaceInfoOutput(workspaces=workspace_service.get_workspaces_by_user(user_id=user_id))
    except WorkspaceFetchDataError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Cannot get list of workspaces")


@workspace_router.get("/types", response_model=WorkspaceTypeOutputModel)
@inject
def get_workspace_types(
        workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])
):
    try:
        return workspace_service.get_workspace_types()
    except WorkspaceTypeFetchDataError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Cannot fetch types of workspace !") from error


@workspace_router.get(path="", response_model=GenericWorkspaceInfoOutput)
@inject
async def get_all_workspaces(
        workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])
):
    try:
        return GenericWorkspaceInfoOutput(workspaces=await workspace_service.get_all_workspaces())
    except WorkspaceFetchDataError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Cannot get list of workspaces")


@workspace_router.get(path="/{workspace_id}/users", response_model=WorkspaceUsersApiModel)
@inject
def get_workspace_users(
        workspace_id: UUID = Path(..., title="Workspace ID"),
        workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])
):
    try:
        return WorkspaceUsersApiModel(users_ids=workspace_service.
                                      get_workspace_users(workspace_id=workspace_id))
    except WorkspaceFetchDataError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Cannot get list of workspaces")


@workspace_router.post(path="", response_model=WorkspaceOutput)
@inject
async def create_workspace(
        workspace: WorkspaceInput = Body(...),
        workspace_service: WorkspaceService = Depends(Provide[DependencyContainer.workspace_service]),
        source_service: SourceService = Depends(Provide[DependencyContainer.source_service])):
    try:
        result = await workspace_service.create_workspace(workspace)
        if workspace.source_id:
            source = await source_service.get_source_by_id(workspace.source_id)
            source.workspace_id = result.id
            await source_service.update_source(source)
        return result
    except (WorkspaceFetchDataError, WorkspaceCreationError, GenericValidationError, SourceDataFetchError,
            SourceUpdatingError) as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message)


@workspace_router.patch(path="/{workspace_id}", response_model=UpdateStatusDataModel)
@inject
async def update_workspace(
        workspace_id: UUID = Path(..., title="Workspace ID"),
        workspace: WorkspaceInput = Body(...),
        workspace_service: WorkspaceService = Depends(Provide[DependencyContainer.workspace_service]),
        source_service: SourceService = Depends(Provide[DependencyContainer.source_service])):
    try:
        result = await workspace_service.update_workspace(workspace, workspace_id)
        if workspace.source_id:
            source = await source_service.get_source_by_id(workspace.source_id)
            source.workspace_id = workspace_id
            await source_service.update_source(source)
        return UpdateStatusDataModel(id=workspace_id, updated=result)
    except (WorkspaceFetchDataError, GenericValidationError, SourceDataFetchError, SourceUpdatingError,
            ValidationError) as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message)
    except WorkspaceNotFoundError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error.message)


@workspace_router.delete(path="/{workspace_id}", response_model=UpdateStatusDataModel)
@inject
async def delete_workspace(workspace_id: UUID = Path(...),
                           workspace_service: WorkspaceService = Depends(
                               Provide[DependencyContainer.workspace_service])):
    try:
        deleted = await workspace_service.delete_workspace(workspace_id=workspace_id)
        return UpdateStatusDataModel(id=workspace_id, updated=deleted)

    except WorkspaceFetchDataError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message)
    except WorkspaceNotFoundError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error.message)


@workspace_router.get(path="/{workspace_id}")
@inject
async def get_workspace_by_id(
        workspace_id: UUID = Path(..., title="Workspace ID"),
        workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])
):
    try:
        return await workspace_service.get_workspace_by_id(workspace_id=workspace_id)
    except WorkspaceFetchDataError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="error getting infos of the workspace created")


@workspace_router.post("/{workspace_id}/users", response_model=bool)
@inject
def assign_users_to_workspace(
        workspace_users: WorkspaceUsersApiModel = Body(...),
        workspace_id: UUID = Path(..., title="Workspace ID"),
        workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])
):
    try:
        return workspace_service.assign_users_to_workspace(users_ids=workspace_users.users_ids,
                                                           workspace_id=workspace_id)
    except WorkspaceFetchDataError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message)
    except WorkspaceCreationError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error.message)


@workspace_router.post(path="/types")
@inject
def create_workspace_type(
        workspace_type: WorkspaceTypeInput = Body(...),
        workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])
):
    try:
        return workspace_service.create_workspace_type(workspace_type)
    except (GenericValidationError, WorkspaceTypeCreationError, WorkspaceTypeFetchDataError) as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="error occurs when creating new workspace created") from error


@workspace_router.get(path="/{workspace_id}/type", response_model=WorkspaceTypeModel)
@inject
def get_workspace_type(
        workspace_id: UUID = Path(..., title="Workspace ID"), workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])):
    try:
        return workspace_service.get_workspace_type(workspace_id=workspace_id)
    except (GenericValidationError, WorkspaceTypeFetchDataError) as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="error occurs when fetching workspace type") from error


@workspace_router.get(path="/types/{type_id}")
@inject
def get_workspace_type_by_id(
        type_id: UUID = Path(..., title="Workspace ID"),
        workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])
) -> WorkspaceTypeModel:
    try:
        return workspace_service.get_workspace_type_by_id(type_id)
    except (WorkspaceTypeFetchDataError, GenericValidationError) as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="error occurs when getting workspace type") from error
