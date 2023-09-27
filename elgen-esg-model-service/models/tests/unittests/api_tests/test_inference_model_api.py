from functools import partial
from unittest import mock

from fastapi import status
from pydantic import ValidationError

from main import app
from source.exceptions.model_exception_handler import PromptError
from source.schemas.model_answer_schema import ModelAnswer
from source.services.model_service import LLMFactoryHuggingFace
from tests.fixtures import client
from tests.test_data import TestApiConfiguration, short_prompt_body, short_prompt, mock_generate_answer_response_llm, \
    predict_response_500
from tests.unittests.api_tests.inference_model_api_mock import mock_inference_context_invalid, mock_model_answer_500, \
    mock_str_model_answer_200

service_mock = mock.Mock(spec=LLMFactoryHuggingFace)


def test_inference_benchmark_with_200_status(client, monkeypatch):
    service_mock.generate_answer.return_value = mock_generate_answer_response_llm

    with app.injection_container.model.override(service_mock):
        response = client.post(
            TestApiConfiguration.chat_inference_router, json=short_prompt_body)
        assert response.status_code == status.HTTP_200_OK


def test_inference_benchmark_with_500_status_validation_error(client, monkeypatch):
    service_mock.generate_answer.side_effect = ValidationError([], ModelAnswer)

    with app.injection_container.model.override(service_mock):
        response = client.post(
            TestApiConfiguration.chat_inference_router,
            json=short_prompt_body
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_inference_benchmark_with_500_status_prediction_error(client, monkeypatch):
    service_mock.generate_answer.side_effect = mock_inference_context_invalid()
    with app.injection_container.model.override(service_mock):
        response = client.post(
            TestApiConfiguration.chat_inference_router, json=short_prompt_body)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_generate_answer_with_413_prompt_error(client, monkeypatch):
    service_mock.generate_answer.side_effect = PromptError
    with app.injection_container.model.override(service_mock):
        response = client.post(
            TestApiConfiguration.chat_inference_router, json=short_prompt_body)
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


def test_chat_inference_old_with_200(client, monkeypatch):
    service_mock.predict.return_value = mock_str_model_answer_200
    with app.injection_container.model.override(service_mock):
        response = client.post(
            TestApiConfiguration.inference_old_router, json=short_prompt)
        assert response.status_code == status.HTTP_200_OK

