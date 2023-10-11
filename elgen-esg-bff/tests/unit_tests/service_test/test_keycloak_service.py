from datetime import date, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from source.exceptions.api_exceptions import UserNotFoundApiException, KeycloakInternalApiException
from source.exceptions.commons import NotOkServiceResponse
from source.exceptions.custom_exceptions import UserRolesNotDefined, KeycloakError, UserAlreadyExistException, \
    UserNotFound, UserInformationFormatError, WrongCredentials, SessionNotFound, DataEncryptionError
from source.helpers.keycloack_helper import format_user_info
from source.schemas.keycloak_schemas import UserInfo, KeycloakAttribute, ClientRole, KeycloakTokenInfo, \
    UserInfoRegistration, UserCreationBulkResponse, ConversationInfo, LoginModel
from source.schemas.source_schemas import SourceLimitSchema
from source.services.keycloak_service import KeycloakService
from tests.conftest import test_keycloak_service
from tests.test_data import user_email, first_name, last_name, valid_date_and_limit_attributes, user_id, \
    valid_date_non_valid_limit_attributes, non_valid_limit_non_valid_date_attributes, user_attributes, dummy_token, \
    keycloak_create_user_partial_import_response, dummy_user_info, user_info, token_info, login_data, login_instance, \
    user_info_error, sources_limit_list, success_ack, sources_limit_dict_list, dummy_user_data_success, \
    dummy_user_data_fail, login_data_dict, login_data_dict_error, decoded_data_success, decoded_user_created_success, \
    mock_token_not_dict, non_valid_user_limit_attributes


@pytest.mark.asyncio
async def test_check_user_limit_valid(test_keycloak_service, monkeypatch):
    async def mock_get_user(user_id, update_attributes_option):
        return user_info

    monkeypatch.setattr(KeycloakService, "get_user", mock_get_user)

    result = await test_keycloak_service.check_user_limit(user_id,
                                                          KeycloakAttribute.CONVERSATIONS)

    assert result is True


def test_get_roles_from_token_success(test_keycloak_service, monkeypatch):
    token = KeycloakTokenInfo(**dummy_token)

    result = test_keycloak_service.get_roles_from_token(token)

    assert result
    assert isinstance(result, list)
    assert result[0] == str(ClientRole.USER)


@pytest.mark.asyncio
async def test_check_user_limit_not_valid_limit_reached(test_keycloak_service, monkeypatch):
    user_info = UserInfo(
        email=user_email,
        first_name=first_name,
        last_name=last_name,
        user_actual_limits=valid_date_non_valid_limit_attributes
    )

    async def mock_get_user(user_id, update_attributes_option):
        return user_info

    monkeypatch.setattr(KeycloakService, "get_user", mock_get_user)
    result = await test_keycloak_service.check_user_limit(user_id,
                                                          KeycloakAttribute.CONVERSATIONS)

    assert result is False


@pytest.mark.asyncio
async def test_check_user_limit_valid_limit_reached_new_day(test_keycloak_service, monkeypatch):
    user_info = UserInfo(
        email=user_email,
        first_name=first_name,
        last_name=last_name,
        user_actual_limits=non_valid_limit_non_valid_date_attributes
    )

    async def mock_get_user(user_id, update_attributes_option):
        return user_info

    monkeypatch.setattr(KeycloakService, "get_user", mock_get_user)

    result = await test_keycloak_service.check_user_limit(user_id,
                                                          KeycloakAttribute.CONVERSATIONS)

    assert result is True


@pytest.mark.asyncio
async def test_check_user_limit_invalid_user_attributes(test_keycloak_service, monkeypatch):
    user_info = UserInfo(
        email=user_email,
        first_name=first_name,
        last_name=last_name,
        user_actual_limits=non_valid_user_limit_attributes
    )

    async def mock_get_user(user_id, update_attributes_option):
        return user_info

    monkeypatch.setattr(KeycloakService, "get_user", mock_get_user)
    with pytest.raises(KeycloakInternalApiException):
        await test_keycloak_service.check_user_limit(user_id,
                                                     KeycloakAttribute.CONVERSATIONS)


@pytest.mark.asyncio
async def test_correctly_update_rate_limit(test_keycloak_service, monkeypatch):
    # Mock the necessary methods
    user_info = UserInfo(email=user_email, first_name=first_name,
                         last_name=last_name,
                         user_actual_limits=valid_date_and_limit_attributes)

    expected_attributes = user_info.user_actual_limits.copy()
    expected_attributes.conversations_limit = [expected_attributes.conversations_limit[0] - 1]
    expected_result = UserInfo(email=user_info.email, first_name=user_info.first_name,
                               last_name=user_info.last_name,
                               user_actual_limits=expected_attributes)

    async def mock_get_admin_token(self):
        return {"access_token": "admin_token"}

    async def mock_get_user(*args, **kwargs):
        return user_info

    async def mock_make_request(*args, **kwargs):
        # You can optionally assert the body sent in the request here
        return {'some_response_key': 'some_response_value'}

    # Apply the mocks to the KeycloakService instance
    monkeypatch.setattr(KeycloakService, "_get_admin_token", mock_get_admin_token)
    monkeypatch.setattr(KeycloakService, "get_user", mock_get_user)
    monkeypatch.setattr(KeycloakService, "_make_update_request", mock_make_request)

    # Create an instance of KeycloakService (you might need to provide necessary fixtures)
    with patch("source.services.keycloak_service.make_request", mock_make_request):
        # Call the update_rate_limit method with conversations attribute
        result = await test_keycloak_service.update_rate_limit(user_id, KeycloakAttribute.CONVERSATIONS)

    # Assert the result is as expected
    assert result == expected_result


@pytest.mark.asyncio
async def test_wrong_update_rate_limit(test_keycloak_service, monkeypatch):
    # Mock the necessary methods
    user_info = UserInfo(email=user_email, first_name=first_name,
                         last_name=last_name,
                         user_actual_limits=non_valid_limit_non_valid_date_attributes.dict())

    async def mock_get_admin_token(self):
        return {"access_token": "admin_token"}

    async def mock_get_user(*args, **kwargs):
        return user_info

    async def mock_make_request(*args, **kwargs):
        # You can optionally assert the body sent in the request here
        return NotOkServiceResponse('failed to get response')

    # Apply the mocks to the KeycloakService instance
    monkeypatch.setattr(KeycloakService, "_get_admin_token", mock_get_admin_token)
    monkeypatch.setattr(KeycloakService, "get_user", mock_get_user)

    # Create an instance of KeycloakService (you might need to provide necessary fixtures)
    with patch("source.services.keycloak_service.make_request", mock_make_request):
        with pytest.raises(UserNotFoundApiException):
            _ = await test_keycloak_service.update_rate_limit(user_id, KeycloakAttribute.CONVERSATIONS)


def test_get_last_date_success(test_keycloak_service):
    mock_user_attributes = ConversationInfo(conversations_date=['2023-07-15'])
    attribute_to_update = KeycloakAttribute.CONVERSATIONS
    result = test_keycloak_service._get_last_date(mock_user_attributes, attribute_to_update)

    assert result == date(2023, 7, 15)


def test_get_last_date_failure(test_keycloak_service):
    mock_user_attributes = ConversationInfo(conversations_date=[])
    attribute_to_update = KeycloakAttribute.CONVERSATIONS

    with pytest.raises(UserInformationFormatError) as error:
        test_keycloak_service._get_last_date(mock_user_attributes, attribute_to_update)


def test_update_attribute_limit(test_keycloak_service):
    attribute_value = 5
    incrementation_condition = True

    result = test_keycloak_service._update_attribute_limit(attribute_value, incrementation_condition)
    assert result == attribute_value + 1


def test_update_user_attributes_future_date(test_keycloak_service):
    last_date = datetime.now() - timedelta(days=1)
    today_date = datetime.now()
    attribute_value = 6

    result = test_keycloak_service._update_user_attributes(
        user_attributes,
        KeycloakAttribute.CONVERSATIONS,
        last_date.strftime('%Y-%m-%d'),
        today_date.strftime('%Y-%m-%d'), attribute_value
    )

    expected_result = {
        f'{KeycloakAttribute.CONVERSATIONS}Limit': [9],
        f'{KeycloakAttribute.CONVERSATIONS}Init': [10],
        f'{KeycloakAttribute.CONVERSATIONS}Date': [str(today_date.strftime('%Y-%m-%d'))]
    }
    assert result == expected_result


def test_update_user_attributes_today_date(test_keycloak_service):
    last_date = datetime.now()
    today_date = datetime.now()

    result = test_keycloak_service._update_user_attributes(
        user_attributes,
        KeycloakAttribute.CONVERSATIONS,
        last_date.strftime('%Y-%m-%d'),
        today_date.strftime('%Y-%m-%d'), user_attributes.get(f'{KeycloakAttribute.CONVERSATIONS}Limit')[0] - 1
    )

    assert (result.get(f'{KeycloakAttribute.CONVERSATIONS}Limit')[0] ==
            user_attributes.get(f'{KeycloakAttribute.CONVERSATIONS}Limit')[0] - 1)


@pytest.mark.asyncio
async def test_check_user_role_success(test_keycloak_service, monkeypatch):
    def token_containing_roles():
        return KeycloakTokenInfo(**dummy_token)

    result = test_keycloak_service.check_user_role(token_containing_roles(), [ClientRole.USER])

    assert result is not None  # if it returns NOne, it means ok!


@pytest.mark.asyncio
async def test_check_user_role_failure_forbidden(test_keycloak_service, monkeypatch):
    def token_containing_roles():
        dummy_token["resource_access"]["elgen"]["roles"] = [ClientRole.USER]
        return KeycloakTokenInfo(**dummy_token)

    with pytest.raises(HTTPException) as error:
        test_keycloak_service.check_user_role(token_containing_roles(), [ClientRole.ADMIN])
        assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_check_user_role_failure_attribute_error(test_keycloak_service, monkeypatch):
    def token_containing_roles():
        token = dict(dummy_token)
        del token["resource_access"]["elgen"]
        return KeycloakTokenInfo(**token)

    with pytest.raises(UserRolesNotDefined):
        test_keycloak_service.check_user_role(token_containing_roles(), [ClientRole.ADMIN])


@pytest.mark.asyncio
async def test_check_user_role_failure_keycloak_error(test_keycloak_service, monkeypatch):
    def mock_exception(*args, **kwargs):
        raise KeyError

    monkeypatch.setattr(KeycloakService, "get_roles_from_token", mock_exception)

    with pytest.raises(KeycloakError):
        test_keycloak_service.check_user_role(KeycloakTokenInfo(**dummy_token), [ClientRole.USER])


@pytest.mark.asyncio
async def test_create_user_success(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = keycloak_create_user_partial_import_response.dict(by_alias=True)

        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)

        result = await test_keycloak_service.create_user(UserInfoRegistration(**dict(dummy_user_info)))

    assert result
    assert isinstance(result, UserCreationBulkResponse)


@pytest.mark.asyncio
async def test_create_user_failure_keycloak_error(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = NotOkServiceResponse(content="Error", status_code=500)

        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)

        with pytest.raises(KeycloakError):
            await test_keycloak_service.create_user(UserInfoRegistration(**dict(dummy_user_info)))


@pytest.mark.asyncio
async def test_create_user_failure_validation_error(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_corrupted_data = keycloak_create_user_partial_import_response.dict(by_alias=True)
        mock_corrupted_data["overwritten"] = "bad string, should not be string!"

        mock_make_request.return_value = mock_corrupted_data

        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)

        with pytest.raises(KeycloakError):
            await test_keycloak_service.create_user(UserInfoRegistration(**dict(dummy_user_info)))


@pytest.mark.asyncio
async def test_create_user_failure_user_already_exists(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_corrupted_data = keycloak_create_user_partial_import_response.dict(by_alias=True)
        mock_corrupted_data["skipped"] = 1

        mock_make_request.return_value = mock_corrupted_data

        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)

        with pytest.raises(UserAlreadyExistException):
            await test_keycloak_service.create_user(UserInfoRegistration(**dict(dummy_user_info)))


@pytest.mark.asyncio
async def test_get_user_success(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = dict(dummy_user_info)

        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)

        result = await test_keycloak_service.get_user(user_id=user_id)

    assert result
    assert isinstance(result, UserInfo)


@pytest.mark.asyncio
async def test_get_user_failure_bad_admin_token(test_keycloak_service, monkeypatch):
    async def bad_get_admin_token(*args, **kwargs):
        return NotOkServiceResponse(content="bad response", status_code=500)

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = dict(dummy_user_info)

        monkeypatch.setattr(KeycloakService, "_get_admin_token", bad_get_admin_token)

        with pytest.raises(UserNotFound):
            await test_keycloak_service.get_user(user_id=user_id)


@pytest.mark.asyncio
async def test_get_user_failure_bad_response_from_keycloak(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = NotOkServiceResponse(content="bad response", status_code=500)

        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)

        with pytest.raises(UserNotFound):
            await test_keycloak_service.get_user(user_id=user_id)


@pytest.mark.asyncio
async def test_check_date_limit_not_expired(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    async def mock_get_user(*args, **kwargs):
        user_info.user_actual_limits = ConversationInfo(
            conversationsDate=[(date.today() + timedelta(days=1)).strftime("%Y-%m-%d")])
        return user_info

    monkeypatch.setattr(KeycloakService, "get_user", mock_get_user)
    monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)

    result = await test_keycloak_service.check_date_limit(user_id="user_id_here")

    assert isinstance(result, dict)
    assert result.get("attributes") == user_info.user_actual_limits.dict(by_alias=True)


@pytest.mark.asyncio
async def test_check_date_limit_invalid_token(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return NotOkServiceResponse(content="")

    monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)
    with pytest.raises(UserNotFound):
        await test_keycloak_service.check_date_limit(user_id="user_id_here")


@pytest.mark.asyncio
async def test_check_date_limit_invalid_date(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    async def mock_get_user(*args, **kwargs):
        user_info.user_actual_limits = ConversationInfo(
            conversationsDate=[])
        return user_info

    monkeypatch.setattr(KeycloakService, "get_user", mock_get_user)
    monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)
    with pytest.raises(UserInformationFormatError):
        await test_keycloak_service.check_date_limit(user_id="user_id_here")


@pytest.mark.asyncio
async def test_reset_user_limits_success(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = dict(dummy_user_info)
        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)

        result = await test_keycloak_service.reset_user_limits(user_profile=user_info,
                                                               user_id="user_id_here")
        assert result.user_actual_limits
        assert result.user_actual_limits.questions_limit == result.user_actual_limits.questions_init
        assert result.user_actual_limits.conversations_limit == result.user_actual_limits.conversations_init


@pytest.mark.asyncio
async def test_reset_user_limits_user_wrong_data(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = dict(dummy_user_info)
        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)
        result = await test_keycloak_service.reset_user_limits(user_profile=user_info_error,
                                                               user_id="user_id_here")
        assert result
        assert result.user_actual_limits.conversations_limit == []


@pytest.mark.asyncio
async def test_make_update_request_invalid_token(test_keycloak_service, monkeypatch):

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = NotOkServiceResponse(content="error")
        result = await test_keycloak_service._make_update_request(admin_token={"access_token": "abc"},
                                                         user_id=user_id,
                                                         user_profile=user_info)
    assert isinstance(result, NotOkServiceResponse)


@pytest.mark.asyncio
async def test_get_token_infos_success(test_keycloak_service, monkeypatch):
    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = token_info.dict()
        result = await test_keycloak_service.get_token_infos(token="test")
        assert isinstance(result, KeycloakTokenInfo)


@pytest.mark.asyncio
async def test_get_token_infos_failure(test_keycloak_service, monkeypatch):
    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = dict()
        with pytest.raises(KeycloakError):
            await test_keycloak_service.get_token_infos(token="test")


@pytest.mark.asyncio
async def test_login_user_not_found(test_keycloak_service, monkeypatch):
    async def get_keycloak_endpoints_configuration(*args, **kwargs):
        return {"token_endpoint": "token_endpoint"}

    monkeypatch.setattr(KeycloakService, "_get_keycloak_endpoints_configuration",
                        get_keycloak_endpoints_configuration)
    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = NotOkServiceResponse(content="")
        with pytest.raises(WrongCredentials):
            await test_keycloak_service.login(user_login=login_data)


@pytest.mark.asyncio
async def test_login_user_found(test_keycloak_service, monkeypatch):
    async def get_keycloak_endpoints_configuration(*args, **kwargs):
        return {"token_endpoint": "token_endpoint"}

    monkeypatch.setattr(KeycloakService, "_get_keycloak_endpoints_configuration",
                        get_keycloak_endpoints_configuration)
    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = login_instance
        result = await test_keycloak_service.login(user_login=login_data)
        assert isinstance(result, LoginModel)


@pytest.mark.asyncio
async def test_logout_user_not_found(test_keycloak_service, monkeypatch):
    async def get_keycloak_endpoints_configuration(*args, **kwargs):
        return {"token_endpoint": "token_endpoint"}

    monkeypatch.setattr(KeycloakService, "_get_keycloak_endpoints_configuration",
                        get_keycloak_endpoints_configuration)
    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = login_instance
        result = await test_keycloak_service.login(user_login=login_data)
        assert isinstance(result, LoginModel)


@pytest.mark.asyncio
async def test_logout_user_found(test_keycloak_service, monkeypatch):
    async def get_get_user_sessions(*args, **kwargs):
        return [{'id': 'session123'}]

    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    monkeypatch.setattr(KeycloakService, 'get_user_sessions', get_get_user_sessions)

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = dict(dummy_user_info)
        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)
        result = await test_keycloak_service.logout(user_id=user_id)
        assert result


@pytest.mark.asyncio
async def test_logout_user_not_found(test_keycloak_service, monkeypatch):
    async def get_get_user_sessions(*args, **kwargs):
        return []

    monkeypatch.setattr(KeycloakService, 'get_user_sessions', get_get_user_sessions)

    with pytest.raises(SessionNotFound):
        await test_keycloak_service.logout(user_id=user_id)


@pytest.mark.asyncio
async def test_get_user_session_found(test_keycloak_service, monkeypatch):
    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = [{'id': 'session123'}]
        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)
        result = await test_keycloak_service.get_user_sessions(user_id=user_id)
        assert len(result) == 1


@pytest.mark.asyncio
async def test_refresh_token_success(test_keycloak_service, monkeypatch):
    mock_credentials = HTTPAuthorizationCredentials(credentials='old_refresh_token',
                                                    scheme="")
    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = login_instance
        result = await test_keycloak_service.refresh_token(credentials=mock_credentials)
        assert isinstance(result, LoginModel)


@pytest.mark.asyncio
async def test_add_complete_sources_configuration_overwrite(test_keycloak_service, monkeypatch):
    """Test if the overwrite of the present config is successful"""

    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    async def mock_get_sources_configurations(*args, **kwargs):
        return sources_limit_dict_list

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        monkeypatch.setattr(KeycloakService, "get_sources_configurations", mock_get_sources_configurations)
        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)
        mock_make_request.return_value = None  # success
        result = await test_keycloak_service.add_complete_sources_configuration(
            complete_sources_config=sources_limit_list)
        assert result == success_ack


@pytest.mark.asyncio
async def test_add_complete_sources_configuration_no_overwrite(test_keycloak_service, monkeypatch):
    """Test if the addition of the config is successful"""

    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    async def mock_get_sources_configurations(*args, **kwargs):
        return []

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        monkeypatch.setattr(KeycloakService, "get_sources_configurations", mock_get_sources_configurations)
        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)
        mock_make_request.return_value = None  # success
        result = await test_keycloak_service.add_complete_sources_configuration(
            complete_sources_config=sources_limit_list)
        assert result == success_ack


@pytest.mark.asyncio
async def test_get_sources_configurations(test_keycloak_service, monkeypatch):
    """test the success  of client source configuration info"""

    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)
        mock_make_request.return_value = {
            "attributes": {"sourceConfig": str(sources_limit_dict_list).replace("'", '"')}}

        result = await test_keycloak_service.get_sources_configurations()
        assert result == sources_limit_dict_list


@pytest.mark.asyncio
async def test_get_sources_configurations_no_config_found(test_keycloak_service, monkeypatch):
    """test the failure of client source configuration info when you can't extract the info"""

    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)
        mock_make_request.return_value = {"attributes": {"other_fields": "other things"}}

        with pytest.raises(HTTPException):
            await test_keycloak_service.get_sources_configurations()


@pytest.mark.asyncio
async def test_extract_source_configurations(test_keycloak_service, monkeypatch):
    """Test if extracting the source configs and returning the appropriate pydantic model is successful"""

    async def mock_get_sources_configurations(*args, **kwargs):
        return sources_limit_dict_list

    monkeypatch.setattr(KeycloakService, "get_sources_configurations", mock_get_sources_configurations)

    result = await test_keycloak_service.extract_source_configurations()
    assert result == sources_limit_list


@pytest.mark.asyncio
async def test_extract_source_configurations_validation_error(test_keycloak_service, monkeypatch):
    """Test if extracting the source configs and returning the appropriate pydantic model fails due to a validation error"""

    async def mock_get_sources_configurations(*args, **kwargs):
        return sources_limit_dict_list

    def mock_validation_error(*args, **kwargs):
        raise ValidationError(errors=[], model=SourceLimitSchema)

    monkeypatch.setattr(KeycloakService, "get_sources_configurations", mock_get_sources_configurations)
    monkeypatch.setattr(SourceLimitSchema, "__init__", mock_validation_error)

    with pytest.raises(HTTPException):
        await test_keycloak_service.extract_source_configurations()


@pytest.mark.asyncio
async def test_update_sources_config(test_keycloak_service, monkeypatch):
    """Test if updating the sources config is successful"""

    async def mock_get_sources_configurations(*args, **kwargs):
        return sources_limit_dict_list

    async def get_admin_token_mock(*args, **kwargs):
        return {"access_token": "abc"}

    monkeypatch.setattr(KeycloakService, "get_sources_configurations", mock_get_sources_configurations)
    monkeypatch.setattr(KeycloakService, "_get_admin_token", get_admin_token_mock)

    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = None  # success as long as it is not NotOkServiceResponse

        result = await test_keycloak_service.update_sources_config(sources_config=sources_limit_list[0])
        assert result == sources_limit_dict_list


@pytest.mark.asyncio
async def test_decrypt_user_creation_data_success(test_keycloak_service, monkeypatch):
    """ Test the decryption of data"""
    result = test_keycloak_service.decrypt_user_creation_data(dummy_user_data_success.get("userData"))
    assert result
    assert result == decoded_user_created_success


@pytest.mark.asyncio
async def test_decrypt_user_creation_data_failure(test_keycloak_service, monkeypatch):
    """ Test the decryption of data"""
    with pytest.raises(DataEncryptionError):
        await test_keycloak_service.decrypt_user_creation_data(dummy_user_data_fail.get("userData"))


@pytest.mark.asyncio
async def test_login_encryption_failure(test_keycloak_service, monkeypatch):
    """ Test the decryption of data"""
    with pytest.raises(DataEncryptionError):
        await test_keycloak_service.decrypt_user_creation_data(dummy_user_data_fail.get("userData"))


@pytest.mark.asyncio
async def test_login_encryption_success(test_keycloak_service, monkeypatch):
    """ Test the decryption of user data in login"""

    async def get_keycloak_endpoints_configuration(*args, **kwargs):
        return {"token_endpoint": "token_endpoint"}

    def mock_decrypt(*args, **kwargs):
        return login_data_dict

    monkeypatch.setattr(KeycloakService, "_get_keycloak_endpoints_configuration",
                        get_keycloak_endpoints_configuration)
    monkeypatch.setattr(KeycloakService, "decrypt_data", mock_decrypt)
    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = login_instance
        result = await test_keycloak_service.login_encrypted(dummy_user_data_fail.get("userData"))
        assert result == LoginModel(**login_instance)


@pytest.mark.asyncio
async def test_login_encryption_failure(test_keycloak_service, monkeypatch):
    """ Test the decryption of user data in login"""

    async def get_keycloak_endpoints_configuration(*args, **kwargs):
        return {"token_endpoint": "token_endpoint"}

    def mock_decrypt(*args, **kwargs):
        return login_data_dict_error

    monkeypatch.setattr(KeycloakService, "_get_keycloak_endpoints_configuration",
                        get_keycloak_endpoints_configuration)
    monkeypatch.setattr(KeycloakService, "decrypt_data", mock_decrypt)
    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = login_instance
        with pytest.raises(KeycloakError):
            await test_keycloak_service.login_encrypted(dummy_user_data_fail.get("userData"))


@pytest.mark.asyncio
async def test_decrypt_data_failure(test_keycloak_service, monkeypatch):
    """ Test the decryption of data"""
    with pytest.raises(DataEncryptionError):
        test_keycloak_service.decrypt_data(dummy_user_data_fail.get("userData"))


@pytest.mark.asyncio
async def test_decrypt_data_success(test_keycloak_service, monkeypatch):
    """ Test the decryption of data"""
    result = test_keycloak_service.decrypt_data(dummy_user_data_success.get("userData"))
    assert result == decoded_data_success


@pytest.mark.asyncio
async def test_check_auth_success(test_keycloak_service, monkeypatch):
    """ Test check auth"""
    mock_credentials = HTTPAuthorizationCredentials(credentials='old_refresh_token',
                                                    scheme="")
    monkeypatch.setattr(KeycloakService, "get_token_infos",
                        mock_token_not_dict)
    result = await test_keycloak_service.check_auth(credentials=mock_credentials)
    assert result == KeycloakTokenInfo(**dummy_token)


@pytest.mark.asyncio
async def test_check_auth_failure(test_keycloak_service, monkeypatch):
    """ Test check auth"""
    mock_credentials = HTTPAuthorizationCredentials(credentials='old_refresh_token',
                                                    scheme="")

    async def mock_token_error(*args, **kwargs):
        raise KeycloakError(status_code=401, detail="")

    monkeypatch.setattr(KeycloakService, "get_token_infos",
                        mock_token_error)
    with pytest.raises(HTTPException):
        await test_keycloak_service.check_auth(credentials=mock_credentials)


@pytest.mark.asyncio
async def test_get_all_users(test_keycloak_service, monkeypatch):
    """ Test get all users"""
    async def mock_get_admin_token(self):
        return {"access_token": "admin_token"}
    monkeypatch.setattr(KeycloakService, "_get_admin_token", mock_get_admin_token)
    with patch('source.services.keycloak_service.make_request') as mock_make_request:
        mock_make_request.return_value = [dict(dummy_user_info)]

        monkeypatch.setattr(KeycloakService, "_get_admin_token", mock_get_admin_token)

        result = await test_keycloak_service.get_all_users()

    assert result
    assert isinstance(result, list)



@pytest.mark.asyncio
async def test_get_workspace_users(test_keycloak_service, monkeypatch):
    """ Test get users in workspace"""

    async def mock_get_all_users(self):
        return [format_user_info(keycloak_response=dummy_user_info,
                                 workspace=True,
                                 user_roles=[ClientRole.USER])]

    monkeypatch.setattr(KeycloakService, "get_all_users",
                        mock_get_all_users)

    result = await test_keycloak_service.get_workspace_users([user_id])
    assert result
    assert isinstance(result, list)
    assert len(result) == 1

@pytest.mark.asyncio
async def test_get_workspace_non_included_users(test_keycloak_service, monkeypatch):
    """ Test users without workspace"""

    async def mock_get_all_users(self):
        return [format_user_info(keycloak_response=dummy_user_info,
                                 workspace=True,
                                 user_roles=[ClientRole.USER])]

    monkeypatch.setattr(KeycloakService, "get_all_users",
                        mock_get_all_users)

    result = await test_keycloak_service.get_workspace_non_included_users([str(uuid4())])
    assert result
    assert isinstance(result, list)
    assert len(result) == 1
