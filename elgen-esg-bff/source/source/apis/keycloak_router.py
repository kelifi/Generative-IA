import logging
from typing import Union, List

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status
from starlette.responses import JSONResponse

from configuration.injection import InjectionContainer
from source.exceptions.api_exceptions import UnauthenticatedKeycloakAPIError, WrongCredentialsApiException, \
    UserNotFoundApiException, KeycloakInternalApiException, UserRolesNotDefinedApiError, UserAlreadyExistApiException, \
    UserFormatApiException
from source.exceptions.custom_exceptions import KeycloakError, WrongCredentials, UserNotFound, SessionNotFound, \
    UserRolesNotDefined, AttributesError, UserAlreadyExistException, DataEncryptionError
from source.schemas.common import AcknowledgeResponse
from source.schemas.keycloak_schemas import LoginData, UserInfo, UserInfoRegistration, LoginModel, ClientRole, \
    UserCreationBulkResponse, UserEncrypted
from source.schemas.source_documents_schemas import SourceLimitSchema
from source.services.keycloak_service import KeycloakService

keycloak_router = APIRouter()
security = HTTPBearer()


@keycloak_router.post("/v1/login", response_model=LoginModel, deprecated=True)
@inject
async def login(user_login: LoginData, keycloak_service: KeycloakService = Depends(Provide[InjectionContainer
                                                                                   .keycloak_service])):
    """
    login without redirection endpoint
    :param user_login:
    :param keycloak_service:
    :return:
    """
    try:
        return await keycloak_service.login(user_login)
    except KeycloakError as keycloak_error:
        logging.error("error checking user user in keycloak")
        raise UnauthenticatedKeycloakAPIError(detail=keycloak_error.detail)
    except WrongCredentials as wrong_credentials:
        logging.error("user credentials are wrong")
        raise WrongCredentialsApiException(detail=wrong_credentials.detail.get("error_description"),
                                           status_code=status.HTTP_400_BAD_REQUEST)


@keycloak_router.post("/v2/login", response_model=LoginModel)
@inject
async def encrypted_login(user_data: UserEncrypted,
                          keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service])):
    try:
        # Decrypt the encrypted credentials and perform login
        return await keycloak_service.login_encrypted(user_data.user_data)
    except KeycloakError as keycloak_error:
        logging.error("error checking user user in keycloak")
        raise UnauthenticatedKeycloakAPIError(detail=keycloak_error.detail)
    except WrongCredentials as wrong_credentials:
        logging.error("user credentials are wrong")
        raise WrongCredentialsApiException(detail=wrong_credentials.detail.get("error_description"),
                                           status_code=status.HTTP_400_BAD_REQUEST)


@keycloak_router.get("/logout")
@inject
async def logout(credentials: HTTPAuthorizationCredentials = Security(security),
                 keycloak_service: KeycloakService = Depends(Provide[InjectionContainer
                                                             .keycloak_service])) -> JSONResponse:
    """
    logout from actual session
    :param credentials:
    :param keycloak_service:
    :return:
    """
    try:
        payload = await keycloak_service.check_logout_auth(credentials)
        user_id = str(payload.dict().get("sub"))
        await keycloak_service.logout(user_id)
        message = "Logout successful"
    except KeycloakError:
        logging.error("Error checking user in Keycloak")
        raise UnauthenticatedKeycloakAPIError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                              detail="error in keycloak")
    except SessionNotFound:
        logging.error("No session found for the user")
        message = "Error finding session for the user"
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": message})


@keycloak_router.get("/user", response_model=Union[UserInfo, List[UserInfo]], response_model_exclude_none=True)
@inject
async def get_user(credentials: HTTPAuthorizationCredentials = Security(security),
                   keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service])):
    """
    get the user by token
    :param credentials:
    :param keycloak_service:
    :return:
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    user_roles = keycloak_service.get_roles_from_token(payload)
    try:
        return await keycloak_service.check_date_limit(user_id=user_id,
                                                       user_roles=user_roles)
    except UserNotFound as user_not_found:
        logging.error("user is not found")
        raise UserNotFoundApiException(detail=user_not_found.detail) from user_not_found
    except KeycloakError as keycloak_error:
        logging.error("internal unexpected error in keycloak")
        raise UnauthenticatedKeycloakAPIError(detail=keycloak_error.detail)
    except AttributesError as missing_key:
        logging.error("internal unexpected error in keycloak")
        raise KeycloakInternalApiException(missing_key)


@keycloak_router.post("/v1/user", deprecated=True)
@inject
async def create_user(user_infos: UserInfoRegistration,
                      credentials: HTTPAuthorizationCredentials = Security(security),
                      keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service])) \
        -> UserCreationBulkResponse:
    """
    create new user
    :param user_infos:
    :param keycloak_service:
    :param credentials:
    :return:
    """
    try:
        payload = await keycloak_service.check_auth(credentials)
        keycloak_service.check_user_role(payload, [ClientRole.ADMIN, ClientRole.SUPER_ADMIN])
        return await keycloak_service.create_user(user_infos)
    except UserRolesNotDefined as error:
        raise UserRolesNotDefinedApiError(
            detail="User Roles are not assigned yet",
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


@keycloak_router.post("/v2/user")
@inject
async def create_user_encrypted(user_infos: UserEncrypted,
                                credentials: HTTPAuthorizationCredentials = Security(security),
                                keycloak_service: KeycloakService = Depends(
                                    Provide[InjectionContainer.keycloak_service])) \
        -> UserCreationBulkResponse:
    """
    create new user
    :param user_infos:
    :param keycloak_service:
    :param credentials:
    :return:
    """
    try:
        payload = await keycloak_service.check_auth(credentials)
        user_infos = keycloak_service.decrypt_user_creation_data(user_infos.user_data)
        keycloak_service.check_user_role(payload, [ClientRole.ADMIN, ClientRole.SUPER_ADMIN])
        return await keycloak_service.create_user(user_infos)
    except DataEncryptionError as encryption_error:
        raise UserFormatApiException(
            detail=encryption_error.detail,
        ) from encryption_error
    except UserRolesNotDefined as error:
        raise UserRolesNotDefinedApiError(
            detail="User Roles are not assigned yet",
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


@keycloak_router.post("/refresh-token", response_model=LoginModel)
@inject
async def refresh_token(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service])):
    """
    create the new user token
    :param credentials:
    :param keycloak_service:
    :return:
    """
    try:
        return await keycloak_service.refresh_token(credentials)
    except KeycloakError as keycloak_error:
        logging.error("error connecting to keycloak")
        raise UnauthenticatedKeycloakAPIError(detail=keycloak_error.detail)
    except WrongCredentials:
        logging.error("user credentials are wrong!")
        raise WrongCredentialsApiException(status_code=status.HTTP_401_UNAUTHORIZED,
                                           detail="invalid token information")


@keycloak_router.get("/source-configuration",
                     summary="Get the existing configurations of sources containing the max web/local values from keycloak",
                     response_model=list[SourceLimitSchema], deprecated=True)
@inject
async def get_sources_configurations(
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        credentials: HTTPAuthorizationCredentials = Security(security)):
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
    return await keycloak_service.extract_source_configurations()


@keycloak_router.patch("/source-configuration",
                       summary="patch the already existing configurations of sources containing the max web/local values from keycloak",
                       response_model=list[SourceLimitSchema], deprecated=True)
@inject
async def update_sources_configurations(sources_config: SourceLimitSchema,
                                        keycloak_service: KeycloakService = Depends(
                                            Provide[InjectionContainer.keycloak_service]),
                                        credentials: HTTPAuthorizationCredentials = Security(security)):
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
    return await keycloak_service.update_sources_config(sources_config=sources_config)


@keycloak_router.post("/source-configuration",
                      summary="post the source configurations of sources containing the max web/local values from "
                              "keycloak, if it already exists this endpoint will overwrite the existing configuration",
                      response_model=AcknowledgeResponse,
                      deprecated=True)
@inject
async def add_sources_configurations(complete_sources_config: list[SourceLimitSchema],
                                     keycloak_service: KeycloakService = Depends(
                                         Provide[InjectionContainer.keycloak_service]),
                                     credentials: HTTPAuthorizationCredentials = Security(security)):
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
    return await keycloak_service.add_complete_sources_configuration(complete_sources_config=complete_sources_config)
