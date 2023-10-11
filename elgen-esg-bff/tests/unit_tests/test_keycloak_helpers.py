import pytest

from source.exceptions.custom_exceptions import MissingUserInformation, SchemaError
from source.helpers.keycloack_helper import format_user_info
from source.schemas.keycloak_schemas import UserInfo
from tests.conftest import test_keycloak_service
from tests.test_data import dummy_user_info


def test_format_user_info_success(test_keycloak_service, monkeypatch):
    data = dict(dummy_user_info)
    result = format_user_info(keycloak_response=data)

    assert result
    assert isinstance(result, UserInfo)


def test_format_user_info_failure_input_not_dict(test_keycloak_service, monkeypatch):
    with pytest.raises(SchemaError):
        format_user_info(keycloak_response=list())


def test_format_user_info_failure_missing_information(test_keycloak_service, monkeypatch):
    data = dict(dummy_user_info)
    del data['firstName']
    with pytest.raises(MissingUserInformation):
        format_user_info(keycloak_response=data)
