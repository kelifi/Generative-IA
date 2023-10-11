from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Security, Path, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from configuration.injection import InjectionContainer
from source.exceptions.custom_exceptions import MetadataObjParseError
from source.schemas.api_schemas import FileInputSchema
from source.schemas.ingestion_schemas import IngestedFilesCountOutput
from source.schemas.keycloak_schemas import ClientRole
from source.schemas.source_schemas import SourceInput, SourceVerificationInput, SourceDataOutput, \
    SourceTypeOutputSchema, SourceOutput
from source.services.conversation_service import ConversationService
from source.services.keycloak_service import KeycloakService
from source.services.sources_service import SourceService

sources_router = APIRouter(prefix="/sources")
security = HTTPBearer()


@sources_router.post("/preview/{file_id}",
                     description="Highlight a pdf file based on the content or send the entire file to be highlighted by FrontEnd")
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
                            workspace_id: UUID = Query(..., description="workspace id of the user",
                                                       alias="workspaceId"),
                            source_service: SourceService = Depends(Provide[InjectionContainer.sources_service])):
    """
    count files that were ingested in elastic search
    """
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.ADMIN, ClientRole.SUPER_ADMIN, ClientRole.USER])
    user_id = str(payload.dict().get("sub"))
    return await source_service.count_files_in_es(user_id=user_id, workspace_id=workspace_id)


@sources_router.get("/type", response_model=SourceTypeOutputSchema)
@inject
async def get_available_sources_per_type(
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        credentials: HTTPAuthorizationCredentials = Security(security),
        type_id: UUID = Query(..., description="workspace id of the user",
                              alias="typeId"),
        source_service: SourceService = Depends(Provide[InjectionContainer.sources_service])):
    """
    Get available sources per type
    """
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.ADMIN, ClientRole.SUPER_ADMIN])
    return await source_service.get_available_sources_per_type(type_id=type_id)


@sources_router.post("/verification", description="verifies if a source can be used to create a workspace")
@inject
async def verify_source(
        source_verification_input: SourceVerificationInput = Body(...),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        credentials: HTTPAuthorizationCredentials = Security(security),
        source_service: SourceService = Depends(Provide[InjectionContainer.sources_service])):
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.ADMIN, ClientRole.SUPER_ADMIN])
    return await source_service.verify_source(source_verification_input)


@sources_router.post("", description="adds a source , can be db or any other source",
                     response_model=SourceDataOutput)
@inject
async def add_source(
        source_input: SourceInput = Body(...),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        credentials: HTTPAuthorizationCredentials = Security(security),
        source_service: SourceService = Depends(Provide[InjectionContainer.sources_service]),
        conversation_service: ConversationService = Depends(Provide[InjectionContainer.conversation_service])):
    payload = await keycloak_service.check_auth(credentials)

    keycloak_service.check_user_role(payload, [ClientRole.ADMIN, ClientRole.SUPER_ADMIN])
    user_id = str(payload.dict().get("sub"))
    source_input.user_id = user_id
    source_output = await conversation_service.add_source_to_database(source=source_input)
    return await source_service.extract_source_information(source=SourceOutput(**source_output))


@sources_router.put("", description="updates a source field mapping",
                    response_model=SourceDataOutput)
@inject
async def update_source_field_mapping(
        source_input: SourceDataOutput = Body(...),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        credentials: HTTPAuthorizationCredentials = Security(security),
        source_service: SourceService = Depends(Provide[InjectionContainer.sources_service])):
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.ADMIN, ClientRole.SUPER_ADMIN])
    return await source_service.update_source_field_mapping(source=source_input)
