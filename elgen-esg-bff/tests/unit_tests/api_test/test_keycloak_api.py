from http import HTTPStatus

import pytest
from fastapi import status

from source.exceptions.api_exceptions import UserRolesNotDefinedApiError
from source.exceptions.custom_exceptions import UserNotFound, DataEncryptionError, UserAlreadyExistException, \
    WrongCredentials, KeycloakError
from source.schemas.keycloak_schemas import PlatformUsers
from source.services.keycloak_service import KeycloakService
from tests.conftest import test_client
from tests.test_data import dummy_user_info, mock_token, mock_check_role_user_success, mock_create_user_success, \
    mock_token_infos, mock_roles_func, mock_user_data, login_data, login_instance, dummy_user_data_success, \
    mock_user_info_registration, login_model_success, dummy_login_data_success, mock_service_response, \
    dummy_token, testing_token, token_for_testing, wrong_users_list_format


@pytest.mark.asyncio
async def test_create_user_v1_api_success(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(KeycloakService, "create_user", mock_create_user_success)

    result = test_client.post("/v1/user", json=dict(dummy_user_info), headers={"Authorization": "Bearer dummy_token"})

    assert result and result.status_code == 200


@pytest.mark.asyncio
async def test_get_user_api_success(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_infos)
    monkeypatch.setattr(KeycloakService, "get_roles_from_token", mock_roles_func)
    monkeypatch.setattr(KeycloakService, "check_date_limit", mock_user_data)

    response = test_client.get("/user", headers={"Authorization": "Bearer dummy_token"})

    assert response and response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_get_user_api_failure(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_infos)
    monkeypatch.setattr(KeycloakService, "get_roles_from_token", mock_roles_func)
    monkeypatch.setattr(KeycloakService, "check_date_limit", UserNotFound(detail='error', status_code=400))

    response = test_client.get("/user", headers={"Authorization": "Bearer dummy_token"})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_login_api_v1_success(test_client, monkeypatch):
    async def mock_login_data(*args, **kwargs):
        return login_instance

    monkeypatch.setattr(KeycloakService, "login", mock_login_data)
    response = test_client.post("/v1/login", json=dict(login_data), headers={"Authorization": "Bearer dummy_token"})
    assert response.json().get('token') == login_instance.get('token').decode()


@pytest.mark.asyncio
async def test_encrypted_login_success(test_client, monkeypatch):
    async def mock_login_data(*args, **kwargs):
        return login_instance

    monkeypatch.setattr(KeycloakService, "login_encrypted", mock_login_data)
    response = test_client.post("/v2/login", json=dict(dummy_login_data_success),
                                headers={"Authorization": "Bearer dummy_token"})
    assert response.json().get('token') == login_instance.get('token').decode()


@pytest.mark.asyncio
async def test_encrypted_login_failure_credentials(test_client, monkeypatch):
    async def mock_login_data_failure_credentials(*args, **kwargs):
        raise WrongCredentials(status_code=500)

    monkeypatch.setattr(KeycloakService, "login_encrypted", mock_login_data_failure_credentials)
    response = test_client.post("/v2/login", json=dict(dummy_login_data_success),
                                headers={"Authorization": "Bearer dummy_token"})
    assert response.is_error
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_encrypted_login_failure_keycloak(test_client, monkeypatch):
    async def mock_login_data_failure_keycloak(*args, **kwargs):
        raise KeycloakError(status_code=403,
                            detail="keycloak error")

    monkeypatch.setattr(KeycloakService, "login_encrypted", mock_login_data_failure_keycloak)
    response = test_client.post("/v2/login", json=dict(dummy_login_data_success),
                                headers={"Authorization": "Bearer dummy_token"})
    assert response.is_error
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_encrypted_login_failure_user_data(test_client, monkeypatch):
    async def mock_login_data_failure_keycloak(*args, **kwargs):
        raise KeycloakError(status_code=422,
                            detail="keycloak error")
    monkeypatch.setattr(KeycloakService, "login_encrypted", mock_login_data_failure_keycloak)
    response = test_client.post("/v2/login", json=dict(dummy_user_info),
                                headers={"Authorization": "Bearer dummy_token"})
    assert response.is_error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_v2_api_success(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token)
    monkeypatch.setattr(KeycloakService, "decrypt_user_creation_data", mock_user_info_registration)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(KeycloakService, "create_user", mock_create_user_success)

    result = test_client.post("/v2/user", json=dict(dummy_user_data_success),
                              headers={"Authorization": "Bearer dummy_token"})

    assert result and result.status_code == 200


@pytest.mark.asyncio
async def test_create_user_v2_api_failure_data_encryption(test_client, monkeypatch):
    def mock_decrypt_error(*args, **kwargs):
        raise DataEncryptionError

    monkeypatch.setattr(KeycloakService, "check_auth", mock_token)
    monkeypatch.setattr(KeycloakService, "decrypt_user_creation_data", mock_decrypt_error)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(KeycloakService, "create_user", mock_create_user_success)

    result = test_client.post("/v2/user", json=dict(dummy_user_data_success),
                              headers={"Authorization": "Bearer dummy_token"})
    assert result.is_error
    assert result.status_code == 400


@pytest.mark.asyncio
async def test_create_user_v2_api_failure_user_already_exist(test_client, monkeypatch):
    def mock_create_user_failure(*args, **kwargs):
        raise UserAlreadyExistException(status_code=500)

    monkeypatch.setattr(KeycloakService, "check_auth", mock_token)
    monkeypatch.setattr(KeycloakService, "decrypt_user_creation_data", mock_user_info_registration)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(KeycloakService, "create_user", mock_create_user_failure)

    result = test_client.post("/v2/user", json=dict(dummy_user_data_success),
                              headers={"Authorization": "Bearer dummy_token"})
    assert result.is_error
    assert result.status_code == 500


@pytest.mark.asyncio
async def test_encrypted_login_failure_user_role(test_client, monkeypatch):
    def mock_user_role_failure(*args, **kwargs):
        raise UserRolesNotDefinedApiError(detail="error in user roles",
                                          status_code=500)

    monkeypatch.setattr(KeycloakService, "check_auth", mock_token)
    monkeypatch.setattr(KeycloakService, "decrypt_user_creation_data", mock_user_info_registration)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_user_role_failure)
    monkeypatch.setattr(KeycloakService, "create_user", mock_create_user_success)

    result = test_client.post("/v2/user", json=dict(dummy_user_data_success),
                              headers={"Authorization": "Bearer dummy_token"})
    assert result.is_error
    assert result.status_code == 500


@pytest.mark.asyncio
async def test_encrypted_login_failure_wrong_credentials(test_client, monkeypatch):
    async def mock_login_wrong_credentials(*args, **kwargs):
        raise WrongCredentials

    monkeypatch.setattr(KeycloakService, "login_encrypted", mock_login_wrong_credentials)
    result = test_client.post("/v2/login", json=dict(login_data), headers={"Authorization": "Bearer dummy_token"})
    assert result.is_error
    assert result.status_code == 422


@pytest.mark.asyncio
async def test_refresh_token_success(test_client, monkeypatch):
    async def mock_refresh_token_success(*args, **kwargs):
        return login_model_success

    monkeypatch.setattr(KeycloakService, "refresh_token", mock_refresh_token_success)
    result = test_client.post("/refresh-token",
                              headers={"Authorization": "Bearer dummy_refresh_token"})
    assert result.json() == login_model_success.dict(by_alias=True)


@pytest.mark.asyncio
async def test_refresh_token_failure(test_client, monkeypatch):
    async def mock_refresh_token_credentials_failure(*args, **kwargs):
        raise WrongCredentials(status_code=401)

    monkeypatch.setattr(KeycloakService, "refresh_token", mock_refresh_token_credentials_failure)
    result = test_client.post("/refresh-token",
                              headers={"Authorization": "Bearer dummy_refresh_token"})
    assert result.is_error
    assert result.status_code == 401


@pytest.mark.asyncio
async def test_get_all_users_success(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", token_for_testing)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)

    async def mock_get_all_users(*args, **kwargs):
        return mock_service_response
    monkeypatch.setattr(KeycloakService, "get_all_users", mock_get_all_users)

    result = test_client.get("/users", headers={"Authorization": "Bearer dummy_token"})

    assert result and result.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_get_all_users_failure_user_role(test_client, monkeypatch):
    def mock_user_role_failure(*args, **kwargs):
        raise UserRolesNotDefinedApiError(detail="You are not allowed to do this action",
                                          status_code=status.HTTP_403_FORBIDDEN)

    async def mock_get_all_users(*args, **kwargs):
        return mock_service_response
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_user_role_failure)
    monkeypatch.setattr(KeycloakService, "get_all_users", mock_get_all_users)

    result = test_client.get("/users", headers={"Authorization": "Bearer dummy_token"})
    assert result.is_error
    assert result.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_all_users_success_content_validation(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", token_for_testing)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)

    async def mock_get_all_users(*args, **kwargs):
        return mock_service_response

    monkeypatch.setattr(KeycloakService, "get_all_users", mock_get_all_users)

    result = test_client.get("/users", headers={"Authorization": "Bearer dummy_token"})

    assert result.status_code == status.HTTP_200_OK

    response_json = result.json()
    assert "users" in response_json
    assert response_json["users"] == mock_service_response

@pytest.mark.asyncio
async def test_get_all_users_content_not_valid(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", token_for_testing)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)

    async def mock_get_users_wrong_format(*args, **kwargs):
        return wrong_users_list_format

    monkeypatch.setattr(KeycloakService, "get_all_users", mock_get_users_wrong_format)

    result = test_client.get("/users", headers={"Authorization": "Bearer dummy_token"})
    assert result.json() == {'detail': 'A schema validation error occurred!'}
    assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

