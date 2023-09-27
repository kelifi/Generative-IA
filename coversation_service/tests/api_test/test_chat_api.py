from unittest import mock
from uuid import uuid4

import pytest as pytest
import requests
from fastapi import status

from main import app
from source.exceptions.service_exceptions import ChatIncompleteDataError, ChatServiceError
from source.repositories.model_repository import ModelRepository
from source.schemas.answer_schema import AnswerRatingResponse, AnswerRatingEnum
from source.schemas.chat_schema import PromptSchema
from source.services.chat_service import ChatService
from tests.api_test.test_api_mocks import mock_answer_object, mock_answer_not_found_error, mock_chat_service_error
from tests.fixtures import client, MockRequest
from tests.service_test.model_service_tests.model_service_mocks import mock_get_models_orm
from tests.test_data import user_id

service_mock = mock.Mock(spec=ChatService)


def test_create_answer(client):
    # Assuming a valid question ID, user ID, and model type
    question_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    # Assuming the ChatService method returns a generated answer
    mock_chat_service = mock.Mock(spec=ChatService)
    mock_chat_service.generate_answer.return_value = {'answer': 'Generated answer'}

    with app.container.answer_service.override(mock_chat_service):
        response = client.get(f"/chat/answer/{question_id}",
                              headers={'user-id': user_id, 'model-code': 'M1'})
        assert response.status_code == 200
        assert response.json() == {'answer': 'Generated answer'}


def test_incomplete_data_create_answer(client):
    # Assuming a valid question ID, user ID, and model type
    question_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    # Assuming the ChatService method returns a generated answer
    mock_chat_service = mock.Mock(spec=ChatService)
    mock_chat_service.generate_answer.side_effect = ChatIncompleteDataError()

    with app.container.answer_service.override(mock_chat_service):
        response = client.get(f"/chat/answer/{question_id}",
                              headers={'user-id': user_id, 'model-code': "M1"})
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_update_rating_for_answer(client):
    user_id = '123e4567-e89b-12d3-a456-426655440000'
    request_body = {
        "answerId": "123e4567-e89b-12d3-a456-426655447777",
        "rating": AnswerRatingEnum.LIKE
    }

    service_mock.set_rating_for_answer.return_value = AnswerRatingResponse()

    with app.container.answer_service.override(service_mock):
        response = client.put("/chat/answer/rating",
                              headers={'user-id': user_id},
                              json=request_body)

        assert response.status_code == 200


def test_data_error_update_rating_for_answer(client):
    user_id = '123e4567-e89b-12d3-a456-426655440000'
    request_body = {
        "answerId": "123e4567-e89b-12d3-a456-426655447777",
        "rating": AnswerRatingEnum.LIKE
    }

    service_mock.set_rating_for_answer.side_effect = ChatServiceError()

    with app.container.answer_service.override(service_mock):
        response = client.put("/chat/answer/rating",
                              headers={'user-id': user_id},
                              json=request_body)
        assert request_body.get('rating').__str__() == 'like'
        assert response.status_code == 500


def test_create_prompt(client):
    question_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    mock_chat_service = mock.Mock(spec=ChatService)
    mock_chat_service.construct_full_prompt.return_value = PromptSchema(prompt="Generated prompt")

    with app.container.answer_service.override(mock_chat_service):
        response = client.get(f"/chat/prompt/{question_id}",
                              headers={'user-id': user_id, 'model-code': 'M1'})
        assert response.status_code == 200
        assert response.json() == {'prompt': 'Generated prompt'}


def test_create_prompt_with_incomplete_data_error(client):
    question_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    mock_chat_service = mock.Mock(spec=ChatService)
    mock_chat_service.construct_full_prompt.side_effect = ChatIncompleteDataError()

    with app.container.answer_service.override(mock_chat_service):
        response = client.get(f"/chat/prompt/{question_id}",
                              headers={'user-id': user_id, 'model-code': 'M1'})
        assert response.status_code == 500
        assert response.json() == {'detail': 'Cannot create prompt!'}


def test_update_answer_content_success(client, monkeypatch):
    user_id = str(uuid4())
    answer_id = str(uuid4())
    new_content = "I hope it works!"

    monkeypatch.setattr(ChatService, "update_answer_with_versioning", mock_answer_object)

    response = client.put(
        "/chat/answer/",
        json={"id": answer_id, "content": new_content},
        headers={'user-id': user_id},
    )

    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data['id'] == answer_id
    assert data['content'] == new_content


def test_update_answer_content_answer_not_found(client, monkeypatch):
    user_id = str(uuid4())
    answer_id = str(uuid4())
    new_content = "I hope it works!"

    monkeypatch.setattr(ChatService, "update_answer_with_versioning", mock_answer_not_found_error)

    response = client.put(
        "/chat/answer/",
        json={"id": answer_id, "content": new_content},
        headers={'user-id': user_id},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_answer_content_chat_service_error(client, monkeypatch):
    user_id = str(uuid4())
    answer_id = str(uuid4())
    new_content = "I hope it works!"

    monkeypatch.setattr(ChatService, "update_answer_with_versioning", mock_chat_service_error)

    response = client.put(
        "/chat/answer/",
        json={"id": answer_id, "content": new_content},
        headers={'user-id': user_id},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_get_answer_by_streaming_testing_endpoint(client, monkeypatch):
    question_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    monkeypatch.setattr(ModelRepository, "get_models", mock_get_models_orm)
    monkeypatch.setattr(requests, "post", MockRequest)

    response = client.post(url=f"/chat/answer/{question_id}/stream/test",
                               params={"text": "Hello world!"},
                               headers={"Authorization": "Bearer dummy_token",
                                        "model-code": "M2"},
                               )

    assert response.status_code == status.HTTP_200_OK

    assert response.content
