from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from configuration.injection import InjectionContainer
from source.schemas.workspace_schemas import WorkspaceByUserApiResponseModel
from source.services.keycloak_service import KeycloakService
from source.services.workspace_service import WorkspaceService

workspace_router = APIRouter(prefix="/workspaces")
security = HTTPBearer()


@workspace_router.get("", response_model=WorkspaceByUserApiResponseModel)
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
    return await workspace_service.get_workspaces_by_user_id(user_id=user_id)
