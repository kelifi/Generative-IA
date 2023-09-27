import uuid

import pytest

from source.exceptions.service_exceptions import (ConversationFetchDataError, ConversationValidationError,
                                                  ConversationNotFoundError)
from source.repositories.conversation_repository import ConversationRepository
from source.schemas.conversation_schema import ConversationSchema
from tests.fixtures import test_conversation_service
from tests.service_test.conversation_service_tests.conversation_service_mocks import (
    mock_returned_conversations_by_user, mock_database_conn_error, mock_conversation_validation_error,
    mock_update_conversation_title, mock_no_result_found, mock_conversation_id, mock_get_question_by_id)
from tests.test_data import (user_id, conversations_data_object, updated_conv_schema, conversation_uuid,
                             conversation_id_object, question_id, question_data_object, workspace_id)


def test_get_conversations_per_user(test_conversation_service, monkeypatch):
    """Test if getting user conversations is successful"""
    monkeypatch.setattr(ConversationRepository, "get_conversations_by_user", mock_returned_conversations_by_user)
    assert test_conversation_service.get_conversations_per_user(user_id=user_id,
                                                                workspace_id=workspace_id) == conversations_data_object


def test_get_conversations_per_user_db_conn_error(test_conversation_service, monkeypatch):
    """Test if database connection error is handled"""
    monkeypatch.setattr(ConversationRepository, "get_conversations_by_user", mock_database_conn_error)
    with pytest.raises(ConversationFetchDataError):
        test_conversation_service.get_conversations_per_user(user_id=user_id, workspace_id=workspace_id)


def test_get_conversations_per_user_validation_error(test_conversation_service, monkeypatch):
    """Test if pydantic validation error is handled"""
    monkeypatch.setattr(ConversationRepository, "get_conversations_by_user", mock_returned_conversations_by_user)
    monkeypatch.setattr(ConversationSchema, "from_orm", mock_conversation_validation_error)
    with pytest.raises(ConversationValidationError):
        test_conversation_service.get_conversations_per_user(user_id=user_id, workspace_id=workspace_id)


def test_create_conversation(test_conversation_service, monkeypatch):
    """Test if creating a conversation is successful"""
    monkeypatch.setattr(ConversationRepository, "create_conversation", mock_conversation_id)
    assert test_conversation_service.create_conversation(user_id=uuid.UUID(user_id),
                                                         workspace_id=workspace_id,
                                                         conversation_title="title") == conversation_id_object


def test_update_conversation_title(test_conversation_service, monkeypatch):
    """Test if updating a conversation's title is successful"""
    monkeypatch.setattr(ConversationRepository, "update_conversation_title", mock_update_conversation_title)
    assert test_conversation_service.update_conversation_title(new_conversation_title="updated title",
                                                               conversation_id=conversation_uuid) == updated_conv_schema


def test_update_conversation_title_with_db_conn_error(test_conversation_service, monkeypatch):
    """Test if updating a conversation's title fails due to a db connection error"""
    monkeypatch.setattr(ConversationRepository, "update_conversation_title", mock_database_conn_error)
    with pytest.raises(ConversationFetchDataError):
        test_conversation_service.update_conversation_title(new_conversation_title="updated title",
                                                            conversation_id=conversation_uuid)


def test_update_conversation_title_no_result_found(test_conversation_service, monkeypatch):
    """Test if updating a conversation's title fails due to non existent conversation_id"""
    monkeypatch.setattr(ConversationRepository, "update_conversation_title", mock_no_result_found)
    with pytest.raises(ConversationNotFoundError):
        test_conversation_service.update_conversation_title(new_conversation_title="updated title",
                                                            conversation_id=conversation_uuid)


def test_delete_conversation_db_conn_error(test_conversation_service, monkeypatch):
    """Test if deleting a conversation fails due to a db connection error"""
    monkeypatch.setattr(ConversationRepository, "delete_conversation", mock_database_conn_error)
    with pytest.raises(ConversationFetchDataError):
        test_conversation_service.delete_conversation(conversation_id=conversation_uuid)


def test_delete_conversation_no_result_found(test_conversation_service, monkeypatch):
    """Test if deleting a conversation fails due to non existent conversation_id"""
    monkeypatch.setattr(ConversationRepository, "delete_conversation", mock_no_result_found)
    with pytest.raises(ConversationNotFoundError):
        test_conversation_service.delete_conversation(conversation_id=conversation_uuid)


def test_get_question_by_id(test_conversation_service, monkeypatch):
    """tests if getting a question by id is successful"""
    monkeypatch.setattr(ConversationRepository, "get_question_by_id", mock_get_question_by_id)
    assert test_conversation_service.get_question_by_id(question_id=question_id) == question_data_object
