from fastapi import status

from source.services.model_service import OpenAIService
from tests.fixtures import client
from tests.test_data import short_prompt_body, TestApiConfiguration
from tests.unit.api_tests.prediction_api_mock import mock_model_answer_200, mock_inference_context_valid, \
    mock_prediction_error, mock_validation_error

def test_prediction_with_200_status(client, monkeypatch):
    monkeypatch.setattr(OpenAIService, "generate_answer", mock_model_answer_200)
    response = client.post(TestApiConfiguration.chat_inference_router, json=short_prompt_body)
    assert response.status_code == status.HTTP_200_OK


def test_prediction_with_500_prediction_error(client, monkeypatch):
    monkeypatch.setattr(OpenAIService, "generate_answer", mock_prediction_error)
    response = client.post(TestApiConfiguration.chat_inference_router, json=short_prompt_body)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_inference_benchmark_with_500_status_validation_error(client, monkeypatch):
    monkeypatch.setattr(OpenAIService, "generate_answer", mock_validation_error)
    response = client.post(TestApiConfiguration.chat_inference_router, json=short_prompt_body)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
