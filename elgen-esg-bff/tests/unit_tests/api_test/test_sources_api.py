import pytest
from fastapi import status

from source.schemas.source_schemas import SourceDataOutput, SourceOutput, SourceVerificationInput
from source.services.conversation_service import ConversationService
from source.services.keycloak_service import KeycloakService
from source.services.sources_service import SourceService
from tests.conftest import test_client
from tests.test_data import mock_token_not_dict, mock_check_user_role_valid, mock_count_files, \
    workspace_id, dummy_nb_files, mock_get_available_sources_per_type, dummy_available_sources, mock_verification_value, \
    dummy_verification_value, dummy_source_data_output, mock_source_data_output, mock_source_output


@pytest.mark.asyncio
async def test_count_files_in_es(test_client, monkeypatch):
    """Test of documents ingestion"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_user_role_valid)
    monkeypatch.setattr(SourceService, "count_files_in_es", mock_count_files)

    result = test_client.get(url=f"/sources/count?workspaceId={workspace_id}",
                             headers={"Authorization": "Bearer dummy_token"},
                             )

    assert result.status_code == status.HTTP_200_OK
    assert result.json() == dummy_nb_files.dict(by_alias=True)


@pytest.mark.asyncio
async def test_get_available_sources_per_type(test_client, monkeypatch):
    """ test Get available sources per type"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_user_role_valid)
    monkeypatch.setattr(SourceService, "get_available_sources_per_type", mock_get_available_sources_per_type)

    result = test_client.get(url="/sources/type?typeId=5bfeca1c-1fd5-4dcd-95ca-d7e9fa65872f",
                             headers={"Authorization": "Bearer dummy_token"})
    assert result.status_code == status.HTTP_200_OK
    assert result.json() == dummy_available_sources


@pytest.mark.asyncio
async def test_verify_source(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_user_role_valid)
    monkeypatch.setattr(SourceService, "verify_source", mock_verification_value)

    result = test_client.post(url="/sources/verification",
                              json=SourceVerificationInput(url= "example").dict(),
                              headers={"Authorization": "Bearer dummy_token"})
    assert result.status_code == status.HTTP_200_OK
    assert result.json() == dummy_verification_value


@pytest.mark.asyncio
async def test_extract_source_information(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_user_role_valid)
    monkeypatch.setattr(SourceService, "extract_source_information", mock_source_data_output)
    monkeypatch.setattr(ConversationService, "add_source_to_database", mock_source_output)

    result = test_client.post(url="/sources",
                              json=dummy_source_data_output.dict(),
                              headers={"Authorization": "Bearer dummy_token"})
    assert result.status_code == status.HTTP_200_OK
    assert result.json() == dummy_source_data_output.dict(by_alias=True)


@pytest.mark.asyncio
async def test_update_source_field_mapping(test_client, monkeypatch):
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_user_role_valid)
    monkeypatch.setattr(SourceService, "update_source_field_mapping", mock_source_data_output)

    result = test_client.put(url="/sources",
                             json=dummy_source_data_output.dict(),
                             headers={"Authorization": "Bearer dummy_token"})
    assert result.status_code == status.HTTP_200_OK
    assert result.json() == dummy_source_data_output.dict(by_alias=True)

