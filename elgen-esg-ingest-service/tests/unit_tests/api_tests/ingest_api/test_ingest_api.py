import pytest
from fastapi import status

from source.services.document_ingestion_service import DocumentsIngestionService
from tests.fixtures import test_client
from tests.test_data import ingestion_response_mock, file_id, index_deletion_response, vector_store_error, \
    _files, schema_error, workspace_id
from tests.unit_tests.api_tests.ingest_api.ingest_api_mocks import mock_ingest_data, mock_delete_ingest_index, \
    vector_store_fail, \
    mock_check_if_ingested_by_filename_error, mock_ingestion_error, mock_text_retrival_from_es_error, mock_schema_error, \
    mock_ingest_index_deletion_error, mock_file_already_exist_error


@pytest.mark.asyncio
async def test_store_documents(test_client, monkeypatch):
    """Test the ingestion router"""

    monkeypatch.setattr(DocumentsIngestionService, "ingest_into_es_and_vector", mock_ingest_data)
    response = test_client.post(url=f"/ingest/files/{file_id}?workspace_id={workspace_id}", files=_files)

    assert response.json() == ingestion_response_mock.__dict__


@pytest.mark.asyncio
async def test_store_documents_vector_store_fail(test_client, monkeypatch):
    """Test the ingestion router when an error occurs when sending data to vector service"""

    monkeypatch.setattr(DocumentsIngestionService, "ingest_into_es_and_vector", vector_store_fail)
    response = test_client.post(url=f"/ingest/files/{file_id}?workspace_id={workspace_id}", files=_files)

    assert response.json() == vector_store_error.__dict__
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_store_documents_check_file_existence_fail(test_client, monkeypatch):
    """Test the ingestion router when an error occurs when checking if a file exist in elastic search fails"""

    monkeypatch.setattr(DocumentsIngestionService, "ingest_into_es_and_vector",
                        mock_check_if_ingested_by_filename_error)
    response = test_client.post(url=f"/ingest/files/{file_id}?workspace_id={workspace_id}", files=_files)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_store_documents_ingestion_error(test_client, monkeypatch):
    """Test the ingestion router when an error occurs when ingesting a file occur"""

    monkeypatch.setattr(DocumentsIngestionService, "ingest_into_es_and_vector", mock_ingestion_error)
    response = test_client.post(url=f"/ingest/files/{file_id}?workspace_id={workspace_id}", files=_files)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_store_documents_ingestion_error(test_client, monkeypatch):
    """Test the ingestion router when an error occurs when ingesting a file occur"""

    monkeypatch.setattr(DocumentsIngestionService, "ingest_into_es_and_vector", mock_ingestion_error)
    response = test_client.post(url=f"/ingest/files/{file_id}?workspace_id={workspace_id}", files=_files)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_store_documents_ingestion_in_es_error(test_client, monkeypatch):
    """Test the ingestion router when an error occurs when ingesting a file occur"""

    monkeypatch.setattr(DocumentsIngestionService, "ingest_into_es_and_vector", mock_text_retrival_from_es_error)
    response = test_client.post(url=f"/ingest/files/{file_id}?workspace_id={workspace_id}", files=_files)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_store_documents_schema_error(test_client, monkeypatch):
    """Test the deletion of the index"""
    monkeypatch.setattr(DocumentsIngestionService, "ingest_into_es_and_vector", mock_schema_error)
    response = test_client.post(url=f"/ingest/files/{file_id}?workspace_id={workspace_id}", files=_files)

    assert response.json() == schema_error.__dict__
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_store_documents_file_already_exist(test_client, monkeypatch):
    """Test the deletion of the index"""
    monkeypatch.setattr(DocumentsIngestionService, "ingest_into_es_and_vector", mock_file_already_exist_error)
    response = test_client.post(url=f"/ingest/files/{file_id}?workspace_id={workspace_id}", files=_files)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {'detail': "Error with Checking a file's existence in ES"}


@pytest.mark.asyncio
async def test_delete_ingest_index(test_client, monkeypatch):
    """Test the deletion of the index"""
    monkeypatch.setattr(DocumentsIngestionService, "delete_ingest_index", mock_delete_ingest_index)
    response = test_client.delete("/ingest/es/")
    assert response.json() == index_deletion_response.__dict__


@pytest.mark.asyncio
async def test_delete_ingest_index(test_client, monkeypatch):
    """Test the deletion of the index"""
    monkeypatch.setattr(DocumentsIngestionService, "delete_ingest_index", mock_ingest_index_deletion_error)
    response = test_client.delete("/ingest/es/")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
