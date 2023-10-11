import logging
from uuid import UUID

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Security, Depends, Body, Path, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from configuration.injection import InjectionContainer
from source.exceptions.api_exceptions import (UserRolesNotDefinedApiError, UserAlreadyExistApiException,
                                              UnauthenticatedKeycloakAPIError, UserFormatApiException)
from source.exceptions.custom_exceptions import (UserRolesNotDefined, UserAlreadyExistException, KeycloakError,
                                                 MissingUserInformation)
from source.schemas.api_schemas import WorkspaceModelsSchema
from source.schemas.common import UpdateStatusDataModel
from source.schemas.keycloak_schemas import ClientRole, UserInfoWorkspaceAPIResponse
from source.schemas.workspace_schemas import (WorkspaceInput, WorkspaceOutput,
                                              WorkspaceUsersApiModel, GenericWorkspaceOutputModel,
                                              GenericWorkspacesResponseModel, WorkspaceTypeOutputModel,
                                              WorkspaceConfigOutputModel)
from source.services.keycloak_service import KeycloakService
from source.services.workspace_service import WorkspaceService

workspace_router = APIRouter(prefix="/workspaces")
security = HTTPBearer()


@workspace_router.get("/types", response_model=WorkspaceTypeOutputModel)
@inject
async def get_available_workspace_type(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        workspace_service: WorkspaceService = Depends(Provide[InjectionContainer.workspace_service])
):
    """
    get available workspace Types
    :param credentials:
    :param keycloak_service:
    :param workspace_service:
    :return: WorkspaceTypeOutput
    """
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
    return await workspace_service.get_workspace_types()


@workspace_router.get("", response_model=GenericWorkspacesResponseModel)
@inject
async def get_available_workspaces_per_user(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        workspace_service: WorkspaceService = Depends(Provide[InjectionContainer.workspace_service])
):
    """
    get the available workspaces by user id
    :param credentials:
    :param keycloak_service:
    :param workspace_service:
    :return: WorkspaceByUserApiResponseModel
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    try:
        keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
        return await workspace_service.get_all_workspaces()
    except HTTPException as error:
        logging.warning("returning user workspaces")
        return await workspace_service.get_workspaces_by_user_id(user_id=user_id)


@workspace_router.get("/{workspace_id}/users", response_model=UserInfoWorkspaceAPIResponse)
@inject
async def get_users_in_workspace(
        workspace_id: UUID = Path(..., title="Workspace ID"),
        credentials: HTTPAuthorizationCredentials = Security(security),
        workspace_service: WorkspaceService = Depends(
            Provide[InjectionContainer.workspace_service]),
        keycloak_service: KeycloakService = Depends(
            Provide[InjectionContainer.keycloak_service])):
    """
    get all users infos from keycloak
    :param workspace_id:
    :param workspace_service:
    :param keycloak_service:
    :param credentials:
    :return:
    """
    try:
        payload = await keycloak_service.check_auth(credentials)
        keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
        all_users_ids = await workspace_service.get_users_in_workspace(workspace_id=workspace_id)
        users = await keycloak_service.get_workspace_users(users_ids=all_users_ids.get("users_ids", []))
        return UserInfoWorkspaceAPIResponse(users=users)
    except UserRolesNotDefined as error:
        raise UserRolesNotDefinedApiError(
            detail="Users Roles are not assigned yet",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from error
    except KeycloakError as keycloak_error:
        raise UnauthenticatedKeycloakAPIError(
            detail=keycloak_error.detail,
            status_code=keycloak_error.status_code
        ) from keycloak_error
    except UserAlreadyExistException as keycloak_error:
        raise UserAlreadyExistApiException(
            detail=keycloak_error.detail,
            status_code=keycloak_error.status_code
        ) from keycloak_error
    except MissingUserInformation as keycloak_error:
        raise UserFormatApiException(
            detail=keycloak_error.detail,
        ) from keycloak_error


@workspace_router.get("/{workspace_id}/users/unavailable", response_model=UserInfoWorkspaceAPIResponse)
@inject
async def get_unavailable_users_in_workspace(
        workspace_id: UUID = Path(..., title="Workspace ID"),
        credentials: HTTPAuthorizationCredentials = Security(security),
        workspace_service: WorkspaceService = Depends(
            Provide[InjectionContainer.workspace_service]),
        keycloak_service: KeycloakService = Depends(
            Provide[InjectionContainer.keycloak_service])):
    """
    get all users infos from keycloak
    :param workspace_id:
    :param workspace_service:
    :param keycloak_service:
    :param credentials:
    :return:
    """
    try:
        payload = await keycloak_service.check_auth(credentials)
        keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
        all_existing_users_ids = await workspace_service.get_users_in_workspace(workspace_id=workspace_id)
        users = await keycloak_service.get_workspace_non_included_users(
            users_ids=all_existing_users_ids.get("users_ids",
                                                 []))
        return UserInfoWorkspaceAPIResponse(users=users)
    except UserRolesNotDefined as error:
        raise UserRolesNotDefinedApiError(
            detail="Users Roles are not assigned yet",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from error
    except KeycloakError as keycloak_error:
        raise UnauthenticatedKeycloakAPIError(
            detail=keycloak_error.detail,
            status_code=keycloak_error.status_code
        ) from keycloak_error
    except UserAlreadyExistException as keycloak_error:
        raise UserAlreadyExistApiException(
            detail=keycloak_error.detail,
            status_code=keycloak_error.status_code
        ) from keycloak_error
    except MissingUserInformation as keycloak_error:
        raise UserFormatApiException(
            detail=keycloak_error.detail,
        ) from keycloak_error


@workspace_router.post("", response_model=WorkspaceOutput)
@inject
async def create_workspace(
        workspace: WorkspaceInput = Body(...),
        credentials: HTTPAuthorizationCredentials = Security(security),
        workspace_service: WorkspaceService = Depends(
            Provide[InjectionContainer.workspace_service]),
        keycloak_service: KeycloakService = Depends(
            Provide[InjectionContainer.keycloak_service])):
    """
    create a workspace by super admin
    :param workspace:
    :param workspace_service:
    :param keycloak_service:
    :param credentials:
    :return:
    """
    try:
        payload = await keycloak_service.check_auth(credentials)
        keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
        return await workspace_service.create_workspace(workspace=workspace)
    except UserRolesNotDefined as error:
        raise UserRolesNotDefinedApiError(
            detail="Users Roles are not assigned yet",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from error
    except UserAlreadyExistException as keycloak_error:
        raise UserAlreadyExistApiException(
            detail=keycloak_error.detail,
            status_code=keycloak_error.status_code
        ) from keycloak_error
    except KeycloakError as keycloak_error:
        raise UnauthenticatedKeycloakAPIError(
            detail=keycloak_error.detail,
            status_code=keycloak_error.status_code
        ) from keycloak_error


@workspace_router.patch("/{workspace_id}", response_model=UpdateStatusDataModel)
@inject
async def updated_workspace(
        credentials: HTTPAuthorizationCredentials = Security(security),
        workspace_id: UUID = Path(..., title="Workspace ID"),
        workspace: WorkspaceInput = Body(...),
        workspace_service: WorkspaceService = Depends(
            Provide[InjectionContainer.workspace_service]),
        keycloak_service: KeycloakService = Depends(
            Provide[InjectionContainer.keycloak_service])
):
    """
    update a workspace by id
    :param workspace: data of workspace to be updated
    :param workspace_id: workspace id
    :param workspace_service:
    :param keycloak_service:
    :param credentials:
    :return:
    """
    try:
        payload = await keycloak_service.check_auth(credentials)
        keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
        return await workspace_service.update_workspace(workspace_id=workspace_id, workspace_data=workspace)
    except UserRolesNotDefined as error:
        raise UserRolesNotDefinedApiError(
            detail="Users Roles are not assigned yet",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from error
    except KeycloakError as keycloak_error:
        raise UnauthenticatedKeycloakAPIError(
            detail=keycloak_error.detail,
            status_code=keycloak_error.status_code
        ) from keycloak_error


@workspace_router.delete("/{workspace_id}", response_model=UpdateStatusDataModel)
@inject
async def delete_workspace(
        credentials: HTTPAuthorizationCredentials = Security(security),
        workspace_id: UUID = Path(..., title="Workspace ID"),
        workspace_service: WorkspaceService = Depends(
            Provide[InjectionContainer.workspace_service]),
        keycloak_service: KeycloakService = Depends(
            Provide[InjectionContainer.keycloak_service])
):
    """
    delete a workspace by id
    :param workspace_id: workspace id
    :param workspace_service:
    :param keycloak_service:
    :param credentials:
    :return:
    """
    try:
        payload = await keycloak_service.check_auth(credentials)
        keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
        return await workspace_service.delete_workspace(workspace_id=workspace_id)
    except UserRolesNotDefined as error:
        raise UserRolesNotDefinedApiError(
            detail="Users Roles are not assigned yet",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from error
    except KeycloakError as keycloak_error:
        raise UnauthenticatedKeycloakAPIError(
            detail=keycloak_error.detail,
            status_code=keycloak_error.status_code
        ) from keycloak_error


@workspace_router.post("/{workspace_id}/users", response_model=dict)
@inject
async def assign_users_to_workspace(
        workspace_users: WorkspaceUsersApiModel = Body(...),
        workspace_id: UUID = Path(..., title="Workspace ID"),
        credentials: HTTPAuthorizationCredentials = Security(security),
        workspace_service: WorkspaceService = Depends(
            Provide[InjectionContainer.workspace_service]),
        keycloak_service: KeycloakService = Depends(
            Provide[InjectionContainer.keycloak_service])):
    try:
        payload = await keycloak_service.check_auth(credentials)
        keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
        result = await workspace_service.assign_users_to_workspace(workspace_users=workspace_users,
                                                                   workspace_id=workspace_id)
        return {"success": result} if isinstance(result, bool) else result
    except UserRolesNotDefined as error:
        raise UserRolesNotDefinedApiError(
            detail="Users Roles are not assigned yet",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from error
    except KeycloakError as keycloak_error:
        raise UnauthenticatedKeycloakAPIError(
            detail=keycloak_error.detail,
            status_code=keycloak_error.status_code
        ) from keycloak_error
    except UserAlreadyExistException as keycloak_error:
        raise UserAlreadyExistApiException(
            detail=keycloak_error.detail,
            status_code=keycloak_error.status_code
        ) from keycloak_error
    except MissingUserInformation as keycloak_error:
        raise UserFormatApiException(
            detail=keycloak_error.detail,
        ) from keycloak_error


@workspace_router.get("/models", response_model=WorkspaceModelsSchema)
@inject
async def get_workspace_models(
        credentials: HTTPAuthorizationCredentials = Security(security),
        workspace_type: str = Query(..., description="the workspace type", alias="workspaceType"),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        workspace_service: WorkspaceService = Depends(Provide[InjectionContainer.workspace_service])
):
    """
      get available workspace models
      :param credentials:
      :param workspace_type:
      :param keycloak_service:
      :param workspace_service:
      :return:
      """
    await keycloak_service.check_auth(credentials)
    return await workspace_service.get_workspace_models(workspace_type=workspace_type)


@workspace_router.get("/{workspace_id}")
@inject
async def get_workspace_by_id(
        workspace_id: UUID = Path(..., title="Workspace ID"),
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(
            Provide[InjectionContainer.keycloak_service]),
        workspace_service: WorkspaceService = Depends(
            Provide[InjectionContainer.workspace_service])):
    """
    Get workspace data by id
    :param workspace_id:
    :param workspace_service:
    :param keycloak_service:
    :param credentials:
    :return: workspace fetched data
    """
    try:
        payload = await keycloak_service.check_auth(credentials)
        user_roles = keycloak_service.get_roles_from_token(payload)
        workspace_config_details = await workspace_service.get_workspace_by_id(workspace_id=workspace_id)
        return WorkspaceConfigOutputModel(
            **workspace_config_details) if ClientRole.SUPER_ADMIN in user_roles else GenericWorkspaceOutputModel(
            **workspace_config_details)

    except UserRolesNotDefined as error:
        raise UserRolesNotDefinedApiError(
            detail="Users Roles are not assigned yet",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from error
    except KeycloakError as keycloak_error:
        raise UnauthenticatedKeycloakAPIError(
            detail=keycloak_error.detail,
            status_code=keycloak_error.status_code
        ) from keycloak_error
