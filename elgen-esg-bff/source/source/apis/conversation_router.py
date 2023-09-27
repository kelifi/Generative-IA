import logging
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Path, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError

from configuration.injection import InjectionContainer
from source.exceptions.api_exceptions import ConversationsLimitApiException
from source.exceptions.api_exceptions import KeycloakInternalApiException
from source.exceptions.custom_exceptions import UserInformationFormatError
from source.schemas.api_schemas import ConversationOutputSchema, ConversationTitleInputSchema, \
    ConversationHistoryOutputSchema, ConversationIdLimitOutputSchema
from source.schemas.keycloak_schemas import KeycloakAttribute
from source.services.conversation_service import ConversationService
from source.services.keycloak_service import KeycloakService

conversations_router = APIRouter(prefix="/conversations")
security = HTTPBearer()


@conversations_router.get("", response_model=list[ConversationOutputSchema])
@inject
async def get_available_conversations_per_user(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        conversation_service: ConversationService = Depends(Provide[InjectionContainer.conversation_service])
):
    """
    get the available conversations by user id
    :param credentials:
    :param keycloak_service:
    :param conversation_service:
    :return:
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    return await conversation_service.get_available_conversations_per_user(user_id=user_id)


@conversations_router.get("/{conversation_id}", response_model=ConversationHistoryOutputSchema)
@inject
async def get_conversation(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        conversation_id: UUID = Path(...),
        conversation_service: ConversationService = Depends(Provide[InjectionContainer.conversation_service])
):
    """
    get conversations per user
    :param credentials:
    :param keycloak_service:
    :param conversation_id:
    :param conversation_service:
    :return:
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    return await conversation_service.get_conversation(user_id=user_id, conversation_id=conversation_id)


@conversations_router.post("", response_model=ConversationIdLimitOutputSchema)
@inject
async def create_conversation(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        title_input: ConversationTitleInputSchema = Body(...),
        conversation_service: ConversationService = Depends(Provide[InjectionContainer.conversation_service])
):
    """
    create new conversation
    :param credentials:
    :param keycloak_service:
    :param title_input:
    :param conversation_service:
    :return:
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    if not await keycloak_service.check_user_limit(user_id=user_id,
                                                   attribute_to_check=KeycloakAttribute.CONVERSATIONS):
        raise ConversationsLimitApiException
    try:
        conversation = await conversation_service.create_conversation(user_id=user_id, title=title_input)
        updated_rate_limit = await keycloak_service.update_rate_limit(user_id, KeycloakAttribute.CONVERSATIONS)
        return ConversationIdLimitOutputSchema(id=conversation.id, conversations_remaining=int(
            updated_rate_limit.user_actual_limits.conversations_limit[0]))
    except (UserInformationFormatError, IndexError, ValidationError):
        logging.error("error getting user rate limits infos")
        raise KeycloakInternalApiException


@conversations_router.put("/{conversation_id}", response_model=ConversationOutputSchema)
@inject
async def update_conversation(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        title_input: ConversationTitleInputSchema = Body(...),
        conversation_id: UUID = Path(...),
        conversation_service: ConversationService = Depends(Provide[InjectionContainer.conversation_service])
):
    """
    update the conversation by user
    :param credentials:
    :param keycloak_service:
    :param title_input:
    :param conversation_id:
    :param conversation_service:
    :return:
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    return await conversation_service.update_conversation(user_id=user_id, title=title_input,
                                                          conversation_id=conversation_id)


# TODO: remove the hard delete, as we have a deleted flag in the conversation table in PG
@conversations_router.delete("/{conversation_id}", response_model=None)
@inject
async def delete_conversation(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        conversation_id: UUID = Path(...),
        conversation_service: ConversationService = Depends(Provide[InjectionContainer.conversation_service])):
    """
    delete a user's conversation
    :param credentials:
    :param keycloak_service:
    :param conversation_id:
    :param conversation_service:
    :return:
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    return await conversation_service.delete_conversation(user_id=user_id, conversation_id=conversation_id)
