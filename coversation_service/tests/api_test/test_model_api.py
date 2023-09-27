from fastapi import status

from source.services.model_service import ModelService
from tests.api_test.test_api_mocks import raise_model_validation_error, mock_model_output, \
    raise_model_output_validation_error, mock_no_result_found, mock_get_model_error, mock_add_model_error, \
    mock_patch_model_error
from tests.fixtures import client
from tests.service_test.model_service_tests.model_service_mocks import mock_get_models
from tests.test_data import model_output_1, model_output_2, model_1_input


def test_get_available_models_for_chat(client, monkeypatch):
    """test if getting the available models for chat is working correctly"""
    monkeypatch.setattr(ModelService, "get_models", mock_get_models)

    response = client.get(url="/models")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [model_output_1.dict(), model_output_2.dict()]


def test_get_available_models_for_chat_validation_error(client, monkeypatch):
    """test if getting the available models for chat is working correctly"""
    monkeypatch.setattr(ModelService, "get_models", raise_model_validation_error)

    response = client.get(url="/models")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'An error occurred with ModelSchema schema'}


def test_get_available_models_retrieval_error(client, monkeypatch):
    """test if getting the available models for chat is failing due to an error in the service layer"""
    monkeypatch.setattr(ModelService, "get_models", mock_get_model_error)

    response = client.get(url="/models")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Could not get model'}


def test_add_model(client, monkeypatch):
    """Test if adding a model is successful"""
    monkeypatch.setattr(ModelService, "add_model", mock_model_output)
    response = client.post(url="/models", json=model_1_input.dict())

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == model_output_1.dict()


def test_add_model_validation_error(client, monkeypatch):
    """Test if validation error is handled"""
    monkeypatch.setattr(ModelService, "add_model", raise_model_output_validation_error)
    response = client.post(url="/models", json=model_1_input.dict())

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'An error occurred with ModelOutputSchema schema'}


def test_add_model_error(client, monkeypatch):
    """Test if adding a model error is handled"""
    monkeypatch.setattr(ModelService, "add_model", mock_add_model_error)
    response = client.post(url="/models", json=model_1_input.dict())

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Could not add model'}


def test_patch_model(client, monkeypatch):
    """Test if patching a model is successful"""
    monkeypatch.setattr(ModelService, "patch_model_configuration", mock_model_output)
    response = client.patch(url="/models", json=model_1_input.dict())

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == model_output_1.dict()


def test_patch_model_validation_error(client, monkeypatch):
    """Test if validation error is handled"""
    monkeypatch.setattr(ModelService, "patch_model_configuration", raise_model_output_validation_error)
    response = client.patch(url="/models", json=model_1_input.dict())

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'An error occurred with ModelOutputSchema schema'}


def test_patch_model_connection_error(client, monkeypatch):
    """Test if model update raises error is handled from the service layer"""
    monkeypatch.setattr(ModelService, "patch_model_configuration", mock_patch_model_error)
    response = client.patch(url="/models", json=model_1_input.dict())

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Could not update model'}


def test_patch_model_no_model_found(client, monkeypatch):
    """Test if model is not found an error is raised and handled"""
    monkeypatch.setattr(ModelService, "patch_model_configuration", mock_no_result_found)
    response = client.patch(url="/models", json=model_1_input.dict())

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'No model exists with code M1'}


def test_get_model_information(client, monkeypatch):
    """Test if getting a model's information is successful"""
    monkeypatch.setattr(ModelService, "get_model_info_per_model_code", mock_model_output)
    response = client.get(url="/models/M1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'code': 'M1', 'max_doc': 2, 'max_web': 1}


def test_get_model_information_validation_error(client, monkeypatch):
    """Test if getting a model's information handled validation errors"""
    monkeypatch.setattr(ModelService, "get_model_info_per_model_code", raise_model_validation_error)
    response = client.get(url="/models/M1")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'An error occurred with ModelSchema schema'}


def test_get_model_information_retrival_error(client, monkeypatch):
    """Test if getting a model's raises an error is actually handled"""
    monkeypatch.setattr(ModelService, "get_model_info_per_model_code", mock_get_model_error)
    response = client.get(url="/models/M1")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Could not get model'}
