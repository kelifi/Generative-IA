from uuid import UUID

from fastapi.encoders import jsonable_encoder

from source.models.enums import RequestMethod
from source.schemas.chat_suggestions_schemas import ChatSuggestion, WorkspaceChatSuggestions
from source.schemas.common import UpdateStatusDataModel
from source.schemas.conversation_schemas import QuestionInputSchema
from source.utils.utils import make_request


class ChatSuggestionsService:
    """
    Service class for handling chat suggestions
    """

    def __init__(self, config: dict) -> None:
        self.config = config

    async def create_chat_suggestion(self, workspace_id: UUID, suggestion: QuestionInputSchema) -> ChatSuggestion:
        """
        Create a suggested question for specific workspace
        Args:
            workspace_id (UUID): The id of the workspace
            suggestion (QuestionInputSchema) : Suggested question

        Returns:
            ChatSuggestion: the newly created suggestion.
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/workspaces/suggestion?workspace_id={workspace_id}",
            method=RequestMethod.POST,
            body=jsonable_encoder(suggestion.dict())
        )

    async def get_suggestions_per_workspace(self, workspace_id: UUID) -> WorkspaceChatSuggestions:
        """
        Get list of suggested questions for specific workspace
        Args:
            workspace_id (UUID): The id of the workspace

        Returns:
            WorkspaceChatSuggestions: list of suggested questions
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/workspaces/suggestion?workspace_id={workspace_id}",
            method=RequestMethod.GET)

    async def delete_suggestion_by_id(self, suggestion_id: UUID) -> UpdateStatusDataModel:
        """
        Delete suggestion by id
        Args:
            suggestion_id (UUID): The id of the suggestion

        Returns:
            UpdateStatusDataModel
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/workspaces/suggestion/{suggestion_id}",
            method=RequestMethod.DELETE)

    async def update_suggestion_by_id(self, suggestion_id: UUID,
                                      suggestion: QuestionInputSchema) -> UpdateStatusDataModel:
        """
        Update suggestion by id
        Args:
            suggestion_id (UUID): The suggestion id
            suggestion (QuestionInputSchema): new suggestion
        Returns:
            UpdateStatusDataModel
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/workspaces/suggestion/{suggestion_id}",
            body=jsonable_encoder(suggestion.dict()),
            method=RequestMethod.PATCH)
