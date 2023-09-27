import logging
from uuid import UUID

from pydantic import ValidationError

from source.exceptions.custom_exceptions import UserInformationFormatError
from source.models.enums import RequestMethod
from source.schemas.api_schemas import ConversationOutputSchema, ConversationTitleInputSchema, \
    ConversationHistoryOutputSchema, ConversationIOutputSchema
from source.utils.utils import make_request


class ConversationService:
    def __init__(self, config: dict) -> None:
        self.config = config

    async def get_conversation(self, user_id: str, conversation_id: UUID) -> ConversationHistoryOutputSchema:
        headers = {
            "user-id": user_id
        }
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/conversations/{conversation_id}",
            method=RequestMethod.GET,
            headers=headers
        )

    async def create_conversation(self, user_id: str,
                                  title: ConversationTitleInputSchema) -> ConversationIOutputSchema:
        headers = {
            "user-id": user_id
        }
        conversation_response = await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri="/conversations",
            method=RequestMethod.POST,
            body=title.dict(),
            headers=headers
        )
        try:
            return ConversationIOutputSchema(**conversation_response)
        except ValidationError as error:
            logging.error(f"Failed to create ConversationResponse: {error}")
            raise UserInformationFormatError

    async def update_conversation(self, user_id: str, title: ConversationTitleInputSchema,
                                  conversation_id: UUID) -> ConversationOutputSchema:
        headers = {
            "user-id": user_id
        }

        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/conversations/{conversation_id}",
            method=RequestMethod.PUT,
            body=title.dict(),
            headers=headers
        )

    async def delete_conversation(self, user_id, conversation_id) -> None:
        headers = {
            "user-id": user_id
        }

        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/conversations/{conversation_id}",
            method=RequestMethod.DELETE,
            headers=headers
        )

    async def get_available_conversations_per_user(self, user_id: str) -> list[ConversationOutputSchema]:
        headers = {
            "user-id": user_id
        }

        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/conversations/",
            method=RequestMethod.GET,
            headers=headers
        )
