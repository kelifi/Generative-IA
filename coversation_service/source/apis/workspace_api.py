from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, Path, Body
from fastapi import status
from pydantic import ValidationError

from configuration.injection_container import DependencyContainer
from configuration.logging_setup import logger
from source.exceptions.api_exception_handler import ElgenAPIException
from source.exceptions.service_exceptions import WorkspaceFetchDataError, WorkspaceCreationError
from source.schemas.workspace_schema import WorkspaceByUserApiResponseModel, WorkspaceOutput, WorkspaceInput, \
    WorkspaceUsersApiModel
from source.services.workspace_service import WorkspaceService

workspace_router = APIRouter(prefix="/workspaces")


@workspace_router.get(path="/users", response_model=WorkspaceByUserApiResponseModel)
@inject
def get_workspaces_by_user(
        user_id: UUID = Header(..., alias='user-id'),
        workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])
):
    try:
        return WorkspaceByUserApiResponseModel(workspaces=workspace_service.get_workspaces_by_user(user_id=user_id))
    except WorkspaceFetchDataError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Cannot get list of workspaces")


@workspace_router.get(path="", response_model=WorkspaceByUserApiResponseModel)
@inject
def get_all_workspaces(
        workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])
):
    try:
        return WorkspaceByUserApiResponseModel(workspaces=workspace_service.get_all_workspaces())
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
def create_workspace(
        workspace: WorkspaceInput = Body(...),
        workspace_service: WorkspaceService = Depends(
            Provide[DependencyContainer.workspace_service])
):
    try:
        return workspace_service.create_workspace(workspace)
    except WorkspaceFetchDataError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message)
    except WorkspaceCreationError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message)
    except ValidationError as error:
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
