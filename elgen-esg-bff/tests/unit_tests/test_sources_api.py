import pytest
from fastapi import status

from source.schemas.source_schemas import SourceVerificationOutput
from source.services.conversation_service import ConversationService
from source.services.keycloak_service import KeycloakService
from source.services.sources_service import SourceService
from tests.conftest import test_client
from tests.test_data import (mock_token_not_dict, mock_check_role_user_success, mock_verify_source_ok,
                             mock_source_verification_input, mock_extract_source_information,
                             mock_add_source_to_db, mock_add_source_input, mock_update_source_field_mapping,
                             update_field_mapping_input_mock)


@pytest.mark.asyncio
async def test_verify_source(test_client, monkeypatch):
    """ test verify source """
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(SourceService, "verify_source", mock_verify_source_ok)

    result = test_client.post(url="/sources/verification",
                              json=mock_source_verification_input.dict(),
                              headers={"Authorization": "Bearer dummy_token"},
                              )
    assert result.status_code == status.HTTP_200_OK
    assert result.json().get("details") == SourceVerificationOutput().details


@pytest.mark.asyncio
async def test_add_source(test_client, monkeypatch):
    """ test add source """
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(ConversationService, "add_source_to_database", mock_add_source_to_db)
    monkeypatch.setattr(SourceService, "extract_source_information", mock_extract_source_information)

    result = test_client.post(url="/sources",
                              json=mock_add_source_input.dict(),
                              headers={"Authorization": "Bearer dummy_token"},
                              )
    assert result.status_code == status.HTTP_200_OK
    assert result.json().get("mapping").get("tables")[0].get("name") == "table name"


@pytest.mark.asyncio
async def test_update_source_field_mapping(test_client, monkeypatch):
    """ test add source """
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(SourceService, "update_source_field_mapping", mock_update_source_field_mapping)

    result = test_client.put(url="/sources",
                             data=update_field_mapping_input_mock.json(),
                             headers={"Authorization": "Bearer dummy_token"},
                             )
    assert result.status_code == status.HTTP_200_OK
    assert result.json().get("mapping").get("tables")[0].get("name") == "table name"
