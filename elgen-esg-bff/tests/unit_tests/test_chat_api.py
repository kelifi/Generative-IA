from uuid import uuid4

import pytest
import requests
from fastapi import status
from httpx import AsyncClient
from pydantic import ValidationError

from source.exceptions.custom_exceptions import UserInformationFormatError
from source.schemas.api_schemas import QuestionLimitOutputSchema
from source.services.chats_service import ChatService
from source.services.keycloak_service import KeycloakService
from tests.conftest import test_client, MockRequest
from tests.test_data import dummy_question, mock_token_not_dict, mock_check_user_limit_false, mock_get_answer, \
    question_id, \
    answer_output_dict, mock_get_models, model_data_1, model_data_2, mock_model, model_info, model_post_dict, \
    mock_check_user_role_valid, model_update_dict, updated_model, dummy_question_input, mock_get_source_docs, \
    mock_get_source_docs_fail, dummy_source_data, mock_get_models_by_workspace_id, mock_check_user_limit_true, \
    mock_update_rate_limit, mock_add_question


@pytest.mark.asyncio
async def test_add_question_rate_limit_fail(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_limit", mock_check_user_limit_false)
    result = test_client.post(url="/chat/question?skipDoc=true&skipWeb=false", json=dict(dummy_question),
                              headers={"Authorization": "Bearer dummy_token",
                                       "conversation-id": "dba202cd-9268-43ca-86db-7d4525f22625",
                                       "workspace-id": str(uuid4())},
                              )

    assert result.json() == {
        'detail': 'questions limit surpassed, you can check later!'} and result.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_add_question_success(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_limit", mock_check_user_limit_true)
    monkeypatch.setattr(ChatService, "add_question", mock_add_question)
    monkeypatch.setattr(KeycloakService, "update_rate_limit", mock_update_rate_limit)
    result = test_client.post(url="/chat/question?skipDoc=true&skipWeb=false", json=dict(dummy_question),
                              headers={"Authorization": "Bearer dummy_token",
                                       "conversation-id": "dba202cd-9268-43ca-86db-7d4525f22625",
                                       "workspace-id": str(uuid4())},
                              )

    assert result.status_code == status.HTTP_200_OK
    api_result = result.json()
    assert api_result.get("isSpecific") is True
    assert api_result.get("content") == 'test_content'
    assert api_result.get("skipDoc") is False
    assert api_result.get("skipWeb") is False
    assert api_result.get("questionsRemaining") == 998

@pytest.mark.asyncio
async def test_add_question_fail_user_information_error(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_limit", mock_check_user_limit_true)
    monkeypatch.setattr(KeycloakService, "update_rate_limit", mock_update_rate_limit)

    async def mock_check_user_information_error(*args, **kwargs):
        raise UserInformationFormatError()

    monkeypatch.setattr(ChatService, "add_question", mock_check_user_information_error)

    result = test_client.post(url="/chat/question?skipDoc=true&skipWeb=false", json=dict(dummy_question),
                              headers={"Authorization": "Bearer dummy_token",
                                       "conversation-id": "dba202cd-9268-43ca-86db-7d4525f22625",
                                       "workspace-id": str(uuid4())},
                              )
    assert result.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

@pytest.mark.asyncio
async def test_add_question_fail_IndexError(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_limit", mock_check_user_limit_true)
    monkeypatch.setattr(KeycloakService, "update_rate_limit", mock_update_rate_limit)

    async def mock_check_IndexError(*args, **kwargs):
        raise IndexError()

    monkeypatch.setattr(ChatService, "add_question", mock_check_IndexError)

    result = test_client.post(url="/chat/question?skipDoc=true&skipWeb=false", json=dict(dummy_question),
                              headers={"Authorization": "Bearer dummy_token",
                                       "conversation-id": "dba202cd-9268-43ca-86db-7d4525f22625",
                                       "workspace-id": str(uuid4())},
                              )
    assert result.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR



@pytest.mark.asyncio
async def test_add_question_fail_ValidationError(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_limit", mock_check_user_limit_true)
    monkeypatch.setattr(KeycloakService, "update_rate_limit", mock_update_rate_limit)

    async def mock_check_validation_error(*args, **kwargs):
        raise ValidationError(errors=[], model=QuestionLimitOutputSchema)

    monkeypatch.setattr(ChatService, "add_question", mock_check_validation_error)

    result = test_client.post(url="/chat/question?skipDoc=true&skipWeb=false", json=dict(dummy_question),
                              headers={"Authorization": "Bearer dummy_token",
                                       "conversation-id": "dba202cd-9268-43ca-86db-7d4525f22625",
                                       "workspace-id": str(uuid4())},
                              )
    assert result.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_get_answer(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(ChatService, "get_answer", mock_get_answer)

    result = test_client.get(url=f"/chat/answer/{question_id}",
                             headers={"Authorization": "Bearer dummy_token",
                                      "model-code": "M1"},
                             )

    assert result.status_code == status.HTTP_200_OK
    assert result.json() == answer_output_dict


@pytest.mark.asyncio
async def test_get_answer_by_streaming_success(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(AsyncClient, "stream", MockRequest)

    response = test_client.get(url=f"/chat/answer/{question_id}/stream?queryDepth=sqlCommand",
                               headers={"Authorization": "Bearer dummy_token",
                                        "model-code": "M1", "user-id": str(uuid4()), "workspace-id": str(uuid4())},
                               )

    assert response.status_code == status.HTTP_200_OK

    assert response.content


@pytest.mark.asyncio
async def test_get_available_models(test_client, monkeypatch):
    """test getting the models"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(ChatService, "get_chat_models", mock_get_models)

    result = test_client.get(
        url="/chat/models",
        headers={"Authorization": "Bearer dummy_token", "model-code": "M1"},
    )

    assert result.status_code == status.HTTP_200_OK
    assert result.json() == [model_data_1, model_data_2]


@pytest.mark.asyncio
async def test_get_available_models_by_workspace_id(test_client, monkeypatch):
    """test getting the models"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(ChatService, "get_available_chat_models_by_workspace_id", mock_get_models_by_workspace_id)

    result = test_client.get(
        url="/chat/models/workspaces",
        headers={"Authorization": "Bearer dummy_token", "model-code": "M1"},
        params={"workspaceId": "6973cbd9-2405-4ecb-8c1a-c731c24dcae9"},
    )

    assert result.status_code == status.HTTP_200_OK
    assert result.json() == {"models": [model_data_1, model_data_2]}


@pytest.mark.asyncio
async def test_add_model(test_client, monkeypatch):
    """test adding a model"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_user_role_valid)
    monkeypatch.setattr(ChatService, "add_model", mock_model)

    result = test_client.post(url=f"/chat/models",
                              headers={"Authorization": "Bearer dummy_token"},
                              json=model_post_dict
                              )

    assert result.status_code == status.HTTP_200_OK
    assert result.json() == model_info.dict(by_alias=True)


@pytest.mark.asyncio
async def test_patch_model(test_client, monkeypatch):
    """Test patching a model"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_user_role_valid)
    monkeypatch.setattr(ChatService, "patch_model", mock_model)

    result = test_client.patch(url=f"/chat/models",
                               headers={"Authorization": "Bearer dummy_token"},
                               json=model_update_dict

                               )

    assert result.status_code == status.HTTP_200_OK
    assert result.json() == updated_model.dict(by_alias=True)


@pytest.mark.asyncio
async def test_get_source_documents(test_client, monkeypatch):
    """Test getting of source documents"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_user_role_valid)
    monkeypatch.setattr(ChatService, "get_source_docs", mock_get_source_docs)

    result = test_client.post(
        url=f"/chat/source-doc?localSourcesCount=3&workspaceId=876e05b0-50a5-11ee-be56-0242ac120002",
        json=dict(dummy_question_input),
        headers={"Authorization": "Bearer dummy_token",
                 "model-code": "M1"},

    )

    assert result.status_code == status.HTTP_200_OK
    assert result.json() == dummy_source_data


@pytest.mark.asyncio
async def test_get_source_documents_fail(test_client, monkeypatch):
    """Test getting of source documents"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_user_role_valid)
    monkeypatch.setattr(ChatService, "get_source_docs", mock_get_source_docs_fail)

    result = test_client.post(
        url=f"/chat/source-doc?localSourcesCount=3&workspaceId=876e05b0-50a5-11ee-be56-0242ac120002",
        json=dict(dummy_question_input),
        headers={"Authorization": "Bearer dummy_token",
                 "model-code": "M1"},

    )

    assert result.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
