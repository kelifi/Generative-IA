from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Security, Path, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from configuration.injection import InjectionContainer
from source.exceptions.custom_exceptions import MetadataObjParseError
from source.schemas.api_schemas import FileInputSchema
from source.schemas.ingestion_schemas import IngestedFilesCountOutput
from source.schemas.keycloak_schemas import ClientRole
from source.services.keycloak_service import KeycloakService
from source.services.sources_service import SourceService

sources_router = APIRouter(prefix="/sources")
security = HTTPBearer()


@sources_router.post("/preview/{file_id}")
@inject
async def preview_sources(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        file_input: FileInputSchema = Body(...),
        file_id: str = Path(..., description="id of the file to preview"),
        source_service: SourceService = Depends(Provide[InjectionContainer.sources_service])
):
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    try:
        return await source_service.preview_document(user_id=user_id, file_input=file_input, file_id=file_id)
    except MetadataObjParseError as error:
        raise HTTPException(status_code=500, detail=error.detail)


@sources_router.get("/download/{file_id}")
@inject
async def download_sources(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        file_id: UUID = Path(),
        source_service: SourceService = Depends(Provide[InjectionContainer.sources_service])
):
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    return await source_service.download_document(file_id=file_id)


@sources_router.get("/count", response_model=IngestedFilesCountOutput)
@inject
async def count_files_in_es(keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
                            credentials: HTTPAuthorizationCredentials = Security(security),
                            source_service: SourceService = Depends(Provide[InjectionContainer.sources_service])):
    """
    count files that were ingested in elastic search
    """
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.ADMIN, ClientRole.SUPER_ADMIN])
    user_id = str(payload.dict().get("sub"))
    return await source_service.count_files_in_es(user_id=user_id)
