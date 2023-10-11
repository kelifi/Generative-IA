from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound

from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseIntegrityError, DatabaseConnectionError, \
    ChatSuggestionsDataBaseError, ChatSuggestionNotFoundError
from source.exceptions.validation_exceptions import GenericValidationError
from source.repositories.chat_suggestions_repository import ChatSuggestionsRepository
from source.schemas.chat_suggestions_schema import ChatSuggestion, WorkspaceChatSuggestions
from source.schemas.common import UpdateStatusDataModel
from source.schemas.conversation_schema import QuestionInputSchema


class ChatSuggestionsService:
    """
    Service class for handling chat suggestions
    """

    def __init__(self,
                 chat_suggestions_repository: ChatSuggestionsRepository
                 ):
        """
        Initialize the ChatSuggestionsService.

        Args:
            chat_suggestions_repository (ChatSuggestionsRepository): The chat workspace repository to use.
        """
        self._chat_suggestions_repository = chat_suggestions_repository

    def create_chat_suggestion(self, workspace_id: UUID, suggestion: QuestionInputSchema) -> ChatSuggestion:
        """
        Create a suggested question for specific workspace
        Args:
            workspace_id (UUID): The id of the workspace
            suggestion (QuestionInputSchema) : Suggested question

        Returns:
            ChatSuggestion: the newly created suggestion.
        """
        try:
            return ChatSuggestion.from_orm(
                self._chat_suggestions_repository.create_chat_suggestion(workspace_id, suggestion))
        except (DatabaseIntegrityError, DatabaseConnectionError) as error:
            logger.error(f"Unable to create new chat suggestion: {error}")
            raise ChatSuggestionsDataBaseError(message="Unable to create new chat suggestion")
        except ValidationError as error:
            logger.error(f"error validating result: {error}")
            raise GenericValidationError

    def get_suggestions_per_workspace(self, workspace_id: UUID) -> WorkspaceChatSuggestions:
        """
        Get list of suggested questions for specific workspace
        Args:
            workspace_id (UUID): The id of the workspace

        Returns:
            WorkspaceChatSuggestions: list of suggested questions
        """
        try:
            suggestions_list = self._chat_suggestions_repository.get_suggestions_by_workspace(workspace_id)
            return WorkspaceChatSuggestions(
                suggestions=[ChatSuggestion.from_orm(suggestion) for suggestion in suggestions_list])
        except DatabaseConnectionError as error:
            logger.error(f"Unable to get chat suggestions for this workspace {workspace_id}: {error}")
            raise ChatSuggestionsDataBaseError(message="Unable to get chat suggestions by workspace")
        except ValidationError as error:
            logger.error(f"error validating result: {error}")
            raise GenericValidationError("Invalid result")

    def delete_suggestion_by_id(self, suggestion_id: UUID) -> UpdateStatusDataModel:
        """
        Delete suggestion by id
        Args:
            suggestion_id (UUID): The id of the suggestion

        Returns:
            UpdateStatusDataModel
        """
        try:
            updated_status = True if not self._chat_suggestions_repository.delete_suggestion_by_id(
                suggestion_id) else False
            return UpdateStatusDataModel(id=suggestion_id, updated=updated_status)
        except DatabaseConnectionError as error:
            logger.error(f"Unable to delete chat suggestion for id {suggestion_id}: {error}")
            raise ChatSuggestionsDataBaseError(message="Unable to delete chat suggestion by id") from error
        except NoResultFound:
            logger.error(f"Suggestion with id {suggestion_id} is not found ")
            raise ChatSuggestionNotFoundError('Suggestion is not found')

    def update_suggestion_by_id(self, suggestion_id: UUID, suggestion: QuestionInputSchema) -> UpdateStatusDataModel:
        try:
            updated_status = True if not self._chat_suggestions_repository.update_suggestion_by_id(suggestion_id,
                                                                                                   suggestion) else False
            return UpdateStatusDataModel(id=suggestion_id, updated=updated_status)
        except DatabaseConnectionError as error:
            logger.error(f"Unable to update chat suggestion {suggestion_id}: {error}")
            raise ChatSuggestionsDataBaseError(message="Unable to update chat suggestion by id") from error
        except NoResultFound:
            logger.error(f"Suggestion with id {suggestion_id} is not found ")
            raise ChatSuggestionNotFoundError('Suggestion is not found')