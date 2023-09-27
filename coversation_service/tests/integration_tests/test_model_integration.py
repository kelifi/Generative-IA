from fastapi import status

from source.helpers.db_helpers import DBHelper
from tests.fixtures import client, scope_session
from tests.integration_tests.data_model_mock import model_input
from tests.test_data import model_1_input, model_output_1


def test_int_get_available_models_for_chat(client, scope_session, monkeypatch):
    """Test if getting available models for chat is successful"""
    monkeypatch.setattr(DBHelper, "create_db_local_session", scope_session)

    response = client.get(url="/models")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{'available': True, 'code': 'model124', 'default': False, 'max_doc': 2, 'max_web': 2,
                                'name': 'Example Model 2'}]


def test_int_add_model(client, scope_session, monkeypatch):
    """Test if adding a model is successful"""
    monkeypatch.setattr(DBHelper, "create_db_local_session", scope_session)
    response = client.post(url="/models", json=model_1_input.dict())

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == model_output_1.dict()


def test_int_add_model_duplicate_model_code(client, scope_session, monkeypatch):
    """Test if adding a model with a model code already existent raises an error"""
    monkeypatch.setattr(DBHelper, "create_db_local_session", scope_session)
    response = client.post(url="/models", json=model_input.dict())

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {
        'detail': f'An integrity error happened when creating new model with code: {model_input.code}'}


def test_patch_model_non_existent(client, scope_session, monkeypatch):
    """Test if patching a non existent model raises an error"""
    monkeypatch.setattr(DBHelper, "create_db_local_session", scope_session)
    response = client.patch(url="/models", json=model_1_input.dict())

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': f'No model exists with code {model_1_input.code}'}
