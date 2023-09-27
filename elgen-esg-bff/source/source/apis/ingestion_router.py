from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, UploadFile, File, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from configuration.injection import InjectionContainer
from source.schemas.common import AcknowledgeResponse
from source.schemas.ingestion_schemas import IngestedFileOutput
from source.schemas.keycloak_schemas import ClientRole
from source.services.ingestion_services import IngestionService
from source.services.keycloak_service import KeycloakService

ingest_router = APIRouter(prefix="/ingest")
security = HTTPBearer()


@ingest_router.delete("/store/es")
@inject
async def delete_ingest_index(ingestion_service: IngestionService = Depends(
    Provide[InjectionContainer.ingestion_service]),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        credentials: HTTPAuthorizationCredentials = Security(security),
) -> AcknowledgeResponse:
    """

    @type ingestion_service: The ingestion service to be used for store docs
    @return:     Will return the acknowledge from ingest service

    """
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.ADMIN, ClientRole.SUPER_ADMIN])
    return await ingestion_service.delete_ingest_index()


@ingest_router.get("/files")
@inject
async def get_doc_list(ingestion_service: IngestionService = Depends(Provide[InjectionContainer.ingestion_service]),
                       keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
                       credentials: HTTPAuthorizationCredentials = Security(security),
                       ) -> \
        List[str]:
    """

    @type ingestion_service: The ingestion service to be used for store docs
    Will return the acknowledge from ingest service
    """
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.ADMIN, ClientRole.SUPER_ADMIN])
    return await ingestion_service.get_doc_list()


@ingest_router.post("/document", response_model=IngestedFileOutput)
@inject
async def get_doc_list(file: UploadFile = File(...),
                       ingestion_service: IngestionService = Depends(Provide[InjectionContainer.ingestion_service]),
                       keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
                       credentials: HTTPAuthorizationCredentials = Security(security),
                       ):
    """

    @type ingestion_service: The ingestion service to be used for store docs
    Will return the acknowledge from ingest service
    """
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.ADMIN, ClientRole.SUPER_ADMIN])
    return await ingestion_service.store_documents(file)
