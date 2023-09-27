from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound

from source.exceptions.service_exceptions import DatabaseConnectionError
from source.models.conversations_models import Conversation
from source.schemas.conversation_schema import ConversationSchema
from tests.test_data import conversations_orm_object, updated_conv_schema, conversation_uuid, question_orm_object


class MockResponse:
    def __init__(self, json_data: dict | str | None, text: str | None, status_code: int):
        self.json_data = json_data
        self.status_code = status_code
        self.text = text

    def json(self) -> dict | str | None:
        return self.json_data


def mock_returned_conversations_by_user(self, user_id: UUID, workspace_id=UUID) -> list[Conversation]:
    return conversations_orm_object


def mock_conversation_validation_error(*args, **kwargs):
    """raises a validation error for ConversationSchema"""
    raise ValidationError(errors=[], model=ConversationSchema)


def mock_database_conn_error(*args, **kwargs):  # real signature unknown as it can be used in multiple places
    raise DatabaseConnectionError


def mock_conversation_id(self, conversation_title: str, user_id: UUID, workspace_id: UUID):
    return conversation_uuid


def mock_update_conversation_title(self, new_conversation_title: str, conversation_id: UUID):
    return updated_conv_schema


def mock_no_result_found(*args, **kwargs):  # real signature unknown as it can be used in multiple places
    raise NoResultFound


def mock_delete_conversation(self, conversation_id: UUID):
    return None


def mock_get_question_by_id(self, question_id: UUID):
    return question_orm_object
