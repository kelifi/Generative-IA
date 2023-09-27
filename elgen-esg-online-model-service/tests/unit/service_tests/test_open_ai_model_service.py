import requests
import pytest
from tests.fixtures import mock_open_ai_service
from tests.test_data import mock_openai_answer, short_prompt, mock_generate_answer_response_open_ai
from tests.unit.service_tests.open_ai_model_service_mocks import mock_openai_api_request, \
    mock_openai_api_request_exception, mock_openai_api_request_not_200_response
from source.exceptions.model_exception_handler import OpenAIRequestError


def test_predict(mock_open_ai_service, monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_openai_api_request)
    model_response = mock_open_ai_service.generate_answer(prompt=short_prompt)
    assert model_response.response == mock_openai_answer


def test_predict_exception(mock_open_ai_service, monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_openai_api_request_exception)
    with pytest.raises(OpenAIRequestError):
        mock_open_ai_service.generate_answer(prompt=short_prompt)


def test_predict_not_200_response(mock_open_ai_service, monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_openai_api_request_not_200_response)
    with pytest.raises(OpenAIRequestError):
        mock_open_ai_service.generate_answer(prompt=short_prompt)


def test_generate_answer(mock_open_ai_service, monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_openai_api_request)
    model_response = mock_open_ai_service.generate_answer(prompt=short_prompt)
    assert model_response.response == mock_generate_answer_response_open_ai.response
    assert model_response.prompt_length == mock_generate_answer_response_open_ai.prompt_length
    assert model_response.inference_time == mock_generate_answer_response_open_ai.inference_time


def test_generate_answer_exception(mock_open_ai_service, monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_openai_api_request_exception)
    with pytest.raises(OpenAIRequestError):
        mock_open_ai_service.generate_answer(prompt=short_prompt)


def test_generate_answer_not_200_response(mock_open_ai_service, monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_openai_api_request_not_200_response)
    with pytest.raises(OpenAIRequestError):
        mock_open_ai_service.generate_answer(prompt=short_prompt)
