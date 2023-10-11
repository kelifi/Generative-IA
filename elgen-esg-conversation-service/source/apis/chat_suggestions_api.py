from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Path, Body, Query
from fastapi import status

from configuration.injection_container import DependencyContainer
from configuration.logging_setup import logger
from source.exceptions.api_exception_handler import ElgenAPIException
from source.exceptions.service_exceptions import ChatSuggestionsDataBaseError, ChatSuggestionNotFoundError
from source.exceptions.validation_exceptions import GenericValidationError
from source.schemas.chat_suggestions_schema import ChatSuggestion, WorkspaceChatSuggestions
from source.schemas.common import UpdateStatusDataModel
from source.schemas.conversation_schema import QuestionInputSchema
from source.services.chat_suggestions_service import ChatSuggestionsService

chat_suggestion_router = APIRouter(prefix="/workspaces/suggestion")


@chat_suggestion_router.post(path="", response_model=ChatSuggestion)
@inject
async def create_chat_suggestion(
        question_input: QuestionInputSchema,
        workspace_id: UUID = Query(...),
        chat_suggestion_service: ChatSuggestionsService = Depends(
            Provide[DependencyContainer.chat_suggestion_service])):
    try:
        return chat_suggestion_service.create_chat_suggestion(workspace_id, question_input)
    except (ChatSuggestionsDataBaseError, GenericValidationError) as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message)


@chat_suggestion_router.get(path="", response_model=WorkspaceChatSuggestions)
@inject
async def get_suggestions_per_workspace(
        workspace_id: UUID = Query(...),
        chat_suggestion_service: ChatSuggestionsService = Depends(
            Provide[DependencyContainer.chat_suggestion_service])):
    try:
        return chat_suggestion_service.get_suggestions_per_workspace(workspace_id)
    except (ChatSuggestionsDataBaseError, GenericValidationError) as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message)


@chat_suggestion_router.delete(path="/{suggestion_id}", response_model=UpdateStatusDataModel)
@inject
async def delete_suggestion_by_id(
        suggestion_id: UUID = Path(...),
        chat_suggestion_service: ChatSuggestionsService = Depends(
            Provide[DependencyContainer.chat_suggestion_service])):
    try:
        return chat_suggestion_service.delete_suggestion_by_id(suggestion_id)
    except ChatSuggestionsDataBaseError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message) from error
    except ChatSuggestionNotFoundError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error.message) from error


@chat_suggestion_router.patch(path="/{suggestion_id}", response_model=UpdateStatusDataModel)
@inject
async def update_suggestion_by_id(
        suggestion_id: UUID = Path(..., title="Suggestion ID"),
        suggestion: QuestionInputSchema = Body(...),
        chat_suggestion_service: ChatSuggestionsService = Depends(
            Provide[DependencyContainer.chat_suggestion_service])):
    try:
        return chat_suggestion_service.update_suggestion_by_id(suggestion_id, suggestion)
    except ChatSuggestionsDataBaseError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error.message) from error
    except ChatSuggestionNotFoundError as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error.message) from error
