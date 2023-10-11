import json

import pytest
from fastapi import status

from source.services.chat_suggestions_service import ChatSuggestionsService
from source.services.keycloak_service import KeycloakService
from tests.conftest import test_client
from tests.test_data import (mock_token_not_dict, mock_check_role_user_success, mock_create_chat_suggestion,
                             workspace_id, mock_chat_suggestion_input_data, chat_suggestion, mock_get_chat_suggestions,
                             mock_delete_suggestion_by_id, suggestion_id, mock_suggestion_deleted,
                             mock_update_suggestion_by_id, mock_suggestion_updated)


@pytest.mark.asyncio
async def test_create_chat_suggestion(test_client, monkeypatch):
    """test creating new chat suggestion for super-admin"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)

    monkeypatch.setattr(ChatSuggestionsService, "create_chat_suggestion", mock_create_chat_suggestion)

    response = test_client.post(url=f"/workspaces/suggestion?workspaceId={workspace_id}",
                                headers={"Authorization": "Bearer dummy_token"},
                                json=mock_chat_suggestion_input_data.dict()
                                )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == json.loads(chat_suggestion.json())


@pytest.mark.asyncio
async def test_get_suggestions_per_workspace(test_client, monkeypatch):
    """test getting suggestions for specific workspace"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)

    monkeypatch.setattr(ChatSuggestionsService, "get_suggestions_per_workspace", mock_get_chat_suggestions)

    response = test_client.get(url=f"/workspaces/suggestion?workspaceId={workspace_id}",
                               headers={"Authorization": "Bearer dummy_token"}
                               )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data.get("suggestions"), list)


@pytest.mark.asyncio
async def test_delete_suggestion_by_id(test_client, monkeypatch):
    """ Test Deleting of suggestion by id"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)

    monkeypatch.setattr(ChatSuggestionsService, "delete_suggestion_by_id", mock_delete_suggestion_by_id)

    response = test_client.delete(url=f"/workspaces/suggestion/{suggestion_id}",
                                  headers={"Authorization": "Bearer dummy_token"}
                                  )

    assert response.status_code == 200
    assert response.json() == json.loads(mock_suggestion_deleted.json())


@pytest.mark.asyncio
async def test_update_suggestion_by_id(test_client, monkeypatch):
    """ Test updating of suggestion by id"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)

    monkeypatch.setattr(ChatSuggestionsService, "update_suggestion_by_id", mock_update_suggestion_by_id)

    response = test_client.patch(url=f"/workspaces/suggestion/{suggestion_id}",
                                 headers={"Authorization": "Bearer dummy_token"},
                                 json=mock_chat_suggestion_input_data.dict()
                                 )

    assert response.status_code == 200
    assert response.json() == json.loads(mock_suggestion_updated.json())
