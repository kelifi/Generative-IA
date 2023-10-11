from uuid import UUID

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Security, Depends, Query, Path, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from configuration.injection import InjectionContainer
from source.schemas.chat_suggestions_schemas import WorkspaceChatSuggestions, ChatSuggestion
from source.schemas.common import UpdateStatusDataModel
from source.schemas.conversation_schemas import QuestionInputSchema
from source.schemas.keycloak_schemas import ClientRole
from source.services.chat_suggestions_service import ChatSuggestionsService
from source.services.keycloak_service import KeycloakService

chat_suggestion_router = APIRouter(prefix="/workspaces/suggestion")
security = HTTPBearer()


@chat_suggestion_router.post("", response_model=ChatSuggestion)
@inject
async def create_chat_suggestion(
        question_input: QuestionInputSchema,
        workspace_id: UUID = Query(..., alias='workspaceId'),
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(
            Provide[InjectionContainer.keycloak_service]),
        chat_suggestion_service: ChatSuggestionsService = Depends(Provide[InjectionContainer.chat_suggestion_service])
):
    """
    Create a suggested question for specific workspace
    :param question_input
    :param workspace_id
    :param credentials:
    :param keycloak_service:
    :param chat_suggestion_service:
    :return: ChatSuggestion
    """
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
    return await chat_suggestion_service.create_chat_suggestion(workspace_id, question_input)


@chat_suggestion_router.get("", response_model=WorkspaceChatSuggestions)
@inject
async def get_suggestions_per_workspace(
        workspace_id: UUID = Query(..., alias='workspaceId'),
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(
            Provide[InjectionContainer.keycloak_service]),
        chat_suggestion_service: ChatSuggestionsService = Depends(Provide[InjectionContainer.chat_suggestion_service])
):
    """
    Get list of suggested questions for specific workspace
    :param workspace_id
    :param credentials:
    :param keycloak_service:
    :param chat_suggestion_service:
    :return: WorkspaceChatSuggestions
    """
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN, ClientRole.ADMIN, ClientRole.USER])
    return await chat_suggestion_service.get_suggestions_per_workspace(workspace_id)


@chat_suggestion_router.delete("/{suggestion_id}", response_model=UpdateStatusDataModel)
@inject
async def delete_suggestion_by_id(
        suggestion_id: UUID = Path(...),
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(
            Provide[InjectionContainer.keycloak_service]),
        chat_suggestion_service: ChatSuggestionsService = Depends(Provide[InjectionContainer.chat_suggestion_service])
):
    """
    Delete a suggestion by id
    :param suggestion_id
    :param credentials:
    :param keycloak_service:
    :param chat_suggestion_service:
    :return: WorkspaceChatSuggestions
    """
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
    return await chat_suggestion_service.delete_suggestion_by_id(suggestion_id)


@chat_suggestion_router.patch("/{suggestion_id}", response_model=UpdateStatusDataModel)
@inject
async def update_suggestion_by_id(
        new_suggestion: QuestionInputSchema = Body(...),
        suggestion_id: UUID = Path(...),
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(
            Provide[InjectionContainer.keycloak_service]),
        chat_suggestion_service: ChatSuggestionsService = Depends(Provide[InjectionContainer.chat_suggestion_service])
):
    """
    Update a suggestion by id
    :param new_suggestion
    :param suggestion_id
    :param credentials:
    :param keycloak_service:
    :param chat_suggestion_service:
    :return: WorkspaceChatSuggestions
    """
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
    return await chat_suggestion_service.update_suggestion_by_id(suggestion_id, new_suggestion)
