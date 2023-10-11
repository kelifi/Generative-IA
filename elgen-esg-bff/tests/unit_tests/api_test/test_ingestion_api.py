import pytest
from fastapi import status

from source.services.ingestion_services import IngestionService
from source.services.keycloak_service import KeycloakService
from tests.conftest import test_client
from tests.test_data import mock_token_not_dict, mock_check_user_role_valid, mock_store_documents, \
    workspace_id, dummy_ingested_files


@pytest.mark.asyncio
async def test_get_doc_list(test_client, monkeypatch):
    """Test of documents ingestion"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_user_role_valid)
    monkeypatch.setattr(IngestionService, "store_documents", mock_store_documents)
    files = {'file': ("test.pdf", open("tests/test.pdf", 'rb'), 'application/pdf')}
    result = test_client.post(url=f"/ingest/document/{workspace_id}",
                              headers={"Authorization": "Bearer dummy_token"},
                              files=files
                              )

    assert result.status_code == status.HTTP_200_OK
    assert result.json() == dummy_ingested_files.dict(by_alias=True)
