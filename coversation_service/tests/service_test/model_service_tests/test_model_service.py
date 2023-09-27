import pytest

from source.exceptions.service_exceptions import ModelRetrievalError
from source.exceptions.validation_exceptions import GenericValidationError
from source.repositories.model_repository import ModelRepository
from source.schemas.models_schema import ModelSchema, ModelOutputSchema
from tests.fixtures import test_model_service
from tests.service_test.model_service_tests.model_service_mocks import mock_get_models_orm, mock_model_validation_error, \
    mock_model, mock_database_conn_error, mock_no_result_found_error
from tests.test_data import model_1, model_2, model_1_input, model_output_1, model_1_update_object, model_code


def test_get_models(test_model_service, monkeypatch):
    """Test getting available models"""
    monkeypatch.setattr(ModelRepository, "get_models", mock_get_models_orm)
    assert test_model_service.get_models() == [model_1, model_2]


def test_get_models_validation_error(test_model_service, monkeypatch):
    """Test getting available models failure due to a validation error is handled"""
    monkeypatch.setattr(ModelRepository, "get_models", mock_get_models_orm)
    monkeypatch.setattr(ModelSchema, "from_orm", mock_model_validation_error)

    with pytest.raises(GenericValidationError):
        assert test_model_service.get_models()


def test_add_model(test_model_service, monkeypatch):
    """Test adding a new model"""
    monkeypatch.setattr(ModelRepository, "add_model", mock_model)
    assert test_model_service.add_model(model_input=model_1_input) == model_output_1


def test_add_model_validation_error(test_model_service, monkeypatch):
    """Test if validation error is handled"""
    monkeypatch.setattr(ModelRepository, "add_model", mock_model)
    monkeypatch.setattr(ModelOutputSchema, "from_orm", mock_model_validation_error)
    with pytest.raises(GenericValidationError):
        test_model_service.add_model(model_input=model_1_input)


def test_patch_model_validation_error(test_model_service, monkeypatch):
    """Test if validation error is handled"""
    monkeypatch.setattr(ModelRepository, "patch_model_source_configurations", mock_model)
    monkeypatch.setattr(ModelOutputSchema, "from_orm", mock_model_validation_error)
    with pytest.raises(GenericValidationError):
        test_model_service.patch_model_configuration(model_sources_config=model_1_update_object)


def test_get_model_info_per_model_code(test_model_service, monkeypatch):
    """Test if getting a model's info per its code is successful"""
    monkeypatch.setattr(ModelRepository, "get_model_per_code", mock_model)
    assert test_model_service.get_model_info_per_model_code(model_code=model_code) == model_1


def test_get_model_info_per_model_code_no_result_found(test_model_service, monkeypatch):
    """Test if getting a model's info per its code handles no result found error"""
    monkeypatch.setattr(ModelRepository, "get_model_per_code", mock_no_result_found_error)
    with pytest.raises(ModelRetrievalError):
        assert test_model_service.get_model_info_per_model_code(model_code=model_code)


def test_get_model_info_per_model_code_db_conn_error(test_model_service, monkeypatch):
    """Test if getting a model's info per its code handles db connection error"""
    monkeypatch.setattr(ModelRepository, "get_model_per_code", mock_database_conn_error)
    with pytest.raises(ModelRetrievalError):
        assert test_model_service.get_model_info_per_model_code(model_code=model_code)


def test_get_model_info_per_model_code_validation_error(test_model_service, monkeypatch):
    """Test if getting a model's info per its code handles validation error"""
    monkeypatch.setattr(ModelRepository, "get_model_per_code", mock_model_validation_error)
    with pytest.raises(GenericValidationError):
        assert test_model_service.get_model_info_per_model_code(model_code=model_code)
