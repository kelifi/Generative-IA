import pytest
import requests

from source.exceptions.service_exceptions import IngestIndexCreationError, VectorApiError, CheckError, \
    TextRetrievalError, IngestPipelineCreationError, SchemaValidationError, PDFExtractionError
from source.schema.elastic_search_schemas import Document
from source.schema.response_schemas import IngestedVectorBatchesCount
from source.services import document_ingestion_service
from source.services.document_ingestion_service import DocumentsIngestionService
from tests.fixtures import test_document_ingest_service
from tests.test_data import dto_vector_service, ingested_data_count, cleaned_document_from_es, file_id, documents_list, \
    processed_documents_list, pdf_content, expected_pdf_content, workspace_id
from tests.unit_tests.service_tests.document_ingestion_service_mocks import mock_success_request, mock_fail_request, \
    mock_connection_error, mock_send_data_to_vector_response, mock_checking_file_response_true, \
    mock_checking_file_response_false, mock_checking_file_response_true_wrong_format, mock_ingest_single_document, \
    mock_get_text_by_es_id, mock_non_empty_clean_text, mock_empty_text, mock_chunk_text, \
    mock_batch_count_validation_error, mock_document_validation_error


def test_create_ingest_index_exist_already(test_document_ingest_service, monkeypatch):
    """Test if the index already exist, then no need to create it"""
    monkeypatch.setattr(DocumentsIngestionService, "check_ingest_index_exists", lambda self: True)
    assert test_document_ingest_service.create_ingest_index() is None


def test_create_ingest_index(test_document_ingest_service, monkeypatch):
    """Test if the index creation is successful"""
    monkeypatch.setattr(DocumentsIngestionService, "check_ingest_index_exists", lambda self: False)
    monkeypatch.setattr(requests, "put", mock_success_request)
    assert test_document_ingest_service.create_ingest_index() is None


def test_create_ingest_index_es_fail(test_document_ingest_service, monkeypatch):
    """Test if the index creation fails due to an error in es is handled"""
    monkeypatch.setattr(DocumentsIngestionService, "check_ingest_index_exists", lambda self: False)
    monkeypatch.setattr(requests, "put", mock_fail_request)
    with pytest.raises(IngestIndexCreationError):
        test_document_ingest_service.create_ingest_index()


def test_create_ingest_index_request_connection_failure(test_document_ingest_service, monkeypatch):
    """Test if the index creation fails due to an error in sending the request to elastic search"""
    monkeypatch.setattr(DocumentsIngestionService, "check_ingest_index_exists", lambda self: False)
    monkeypatch.setattr(requests, "put", mock_connection_error)
    with pytest.raises(IngestIndexCreationError):
        test_document_ingest_service.create_ingest_index()


def test_send_data_to_vector_service(test_document_ingest_service, monkeypatch):
    """Test if sending data to vector service is successful"""
    monkeypatch.setattr(requests, "post", mock_send_data_to_vector_response)
    assert test_document_ingest_service.send_data_to_vector_service(data=dto_vector_service) == ingested_data_count


def test_send_data_to_vector_service_fail_response(test_document_ingest_service, monkeypatch):
    """Test if sending data to vector service fails after getting the response from the request"""
    monkeypatch.setattr(requests, "post", mock_fail_request)
    with pytest.raises(VectorApiError):
        assert test_document_ingest_service.send_data_to_vector_service(data=dto_vector_service)


def test_send_data_to_vector_service_conn_error(test_document_ingest_service, monkeypatch):
    """Test if sending data to vector service fails if when the connection to vector service fails"""
    monkeypatch.setattr(requests, "post", mock_connection_error)
    with pytest.raises(VectorApiError):
        assert test_document_ingest_service.send_data_to_vector_service(data=dto_vector_service)


def test_send_data_to_vector_service_fail_request(test_document_ingest_service, monkeypatch):
    """Test if sending data to vector service fails due to a request failure error but is handled"""
    monkeypatch.setattr(requests, "post", mock_fail_request)
    with pytest.raises(VectorApiError):
        assert test_document_ingest_service.send_data_to_vector_service(data=dto_vector_service)


def test_send_data_to_vector_service_validation_response(test_document_ingest_service, monkeypatch):
    """Test if sending data to vector service fails due to a validation error but is handled"""
    monkeypatch.setattr(requests, "post", mock_send_data_to_vector_response)
    monkeypatch.setattr(IngestedVectorBatchesCount, "__init__", mock_batch_count_validation_error)
    with pytest.raises(SchemaValidationError):
        assert test_document_ingest_service.send_data_to_vector_service(data=dto_vector_service)


def test_check_if_ingested_by_filename_is_true(test_document_ingest_service, monkeypatch):
    """Test if checking whether a file was already ingested is successful"""
    monkeypatch.setattr(requests, "get", mock_checking_file_response_true)
    assert test_document_ingest_service.check_if_ingested_by_filename(file_name="file_name") is True


def test_check_if_ingested_by_filename_is_false(test_document_ingest_service, monkeypatch):
    """Test if checking if a file was already ingested is successful"""
    monkeypatch.setattr(requests, "get", mock_checking_file_response_false)
    assert test_document_ingest_service.check_if_ingested_by_filename(file_name="file_name") is False


def test_check_if_ingested_by_filename_response_fail(test_document_ingest_service, monkeypatch):
    """Test if checking if a file was already ingested fails due to elastic search sending back a non 200 response"""
    monkeypatch.setattr(requests, "get", mock_fail_request)
    with pytest.raises(CheckError):
        test_document_ingest_service.check_if_ingested_by_filename(file_name="file_name")


def test_check_if_ingested_by_filename_request_fail(test_document_ingest_service, monkeypatch):
    """Test if checking if a file was already ingested fails due to elastic search get request faims being sent"""
    monkeypatch.setattr(requests, "get", mock_connection_error)
    with pytest.raises(CheckError):
        test_document_ingest_service.check_if_ingested_by_filename(file_name="file_name")


def test_check_if_ingested_by_filename_key_error(test_document_ingest_service, monkeypatch):
    """Test if checking if a file was already ingested fails due to extracting the count information fails"""
    monkeypatch.setattr(requests, "get", mock_checking_file_response_true_wrong_format)
    with pytest.raises(CheckError):
        test_document_ingest_service.check_if_ingested_by_filename(file_name="file_name")


def test_get_full_document_from_es(test_document_ingest_service, monkeypatch):
    """Test if getting the document from es is successful"""
    monkeypatch.setattr(DocumentsIngestionService, "ingest_single_document", mock_ingest_single_document)
    monkeypatch.setattr(DocumentsIngestionService, "get_text_by_es_id", mock_get_text_by_es_id)
    monkeypatch.setattr(document_ingestion_service, "clean_non_sense_text", mock_non_empty_clean_text)
    assert test_document_ingest_service.get_full_document_from_es(file_content=b'', file_id=file_id,
                                                                  file_name="file_name.pdf",
                                                                  workspace_id=workspace_id) == cleaned_document_from_es


def test_get_full_document_from_es_empty_indexed_text(test_document_ingest_service, monkeypatch):
    """Test if getting the document from es when the ingested file has no text extracted raises an error"""
    monkeypatch.setattr(DocumentsIngestionService, "ingest_single_document", mock_ingest_single_document)
    monkeypatch.setattr(DocumentsIngestionService, "get_text_by_es_id", mock_empty_text)
    with pytest.raises(TextRetrievalError):
        assert test_document_ingest_service.get_full_document_from_es(file_content=b'', file_id=file_id,
                                                                      file_name="file_name",
                                                                      workspace_id=workspace_id) == cleaned_document_from_es


def test_get_full_document_from_es_empty_clean_text(test_document_ingest_service, monkeypatch):
    """Test if getting the document from es when the cleaned text is empty raises an error"""
    monkeypatch.setattr(DocumentsIngestionService, "ingest_single_document", mock_ingest_single_document)
    monkeypatch.setattr(DocumentsIngestionService, "get_text_by_es_id", mock_get_text_by_es_id)
    monkeypatch.setattr(document_ingestion_service, "clean_non_sense_text", mock_empty_text)
    with pytest.raises(TextRetrievalError):
        assert test_document_ingest_service.get_full_document_from_es(file_content=b'', file_id=file_id,
                                                                      file_name="file_name",
                                                                      workspace_id=workspace_id) == cleaned_document_from_es


def test_get_full_document_from_es_validation_error(test_document_ingest_service, monkeypatch):
    """Test if getting the document from es is successful"""
    monkeypatch.setattr(DocumentsIngestionService, "ingest_single_document", mock_ingest_single_document)
    monkeypatch.setattr(DocumentsIngestionService, "get_text_by_es_id", mock_get_text_by_es_id)
    monkeypatch.setattr(document_ingestion_service, "clean_non_sense_text", mock_non_empty_clean_text)
    monkeypatch.setattr(Document, "__init__", mock_document_validation_error)
    with pytest.raises(SchemaValidationError):
        test_document_ingest_service.get_full_document_from_es(file_content=b'', file_id=file_id, file_name="file_name",
                                                               workspace_id=workspace_id)


def test_process_documents(test_document_ingest_service, monkeypatch):
    """Test processing documents by chunking them"""
    monkeypatch.setattr(document_ingestion_service, "chunk_text_nltk", mock_chunk_text)
    assert test_document_ingest_service.process_documents(documents_list=documents_list) == processed_documents_list


def test_process_documents_validation_error(test_document_ingest_service, monkeypatch):
    """Test if processing documents fails due to a validation error is handled"""
    monkeypatch.setattr(document_ingestion_service, "chunk_text_nltk", mock_chunk_text)
    monkeypatch.setattr(Document, "__init__", mock_document_validation_error)
    with pytest.raises(SchemaValidationError):
        test_document_ingest_service.process_documents(documents_list=documents_list)


def test_create_pipeline(test_document_ingest_service, monkeypatch):
    """Check if pipeline creation in elastic search is successful"""
    monkeypatch.setattr(requests, "put", mock_success_request)
    assert test_document_ingest_service.create_pipeline() is None


def test_create_pipeline_failed_response(test_document_ingest_service, monkeypatch):
    """Check if when the pipeline creation in elastic search fails due to a non 200 response is handled"""
    monkeypatch.setattr(requests, "put", mock_fail_request)
    with pytest.raises(IngestPipelineCreationError):
        test_document_ingest_service.create_pipeline()


def test_create_pipeline_conn_error(test_document_ingest_service, monkeypatch):
    """Check if when the pipeline creation in elastic search fails due connection error to is handled"""
    monkeypatch.setattr(requests, "put", mock_connection_error)
    with pytest.raises(IngestPipelineCreationError):
        test_document_ingest_service.create_pipeline()


@pytest.mark.comment("we won't check on the es_id as it is randomly generated with each function call")
@pytest.mark.skip("This test needs to be checked as it runs locally but not in jenkins")
def test_extract_text_from_pdf(test_document_ingest_service, monkeypatch):
    """Test if extracting data from a pdf file is successful, the get_text_from_one_page function is not mocked but is tested here"""
    result = test_document_ingest_service.extract_text_from_pdf(file_content=pdf_content, file_name="file_name.pdf",
                                                                file_id="d875d722-be7e-48bb-89f1-d78960ba4eea",
                                                                workspace_id=workspace_id)
    assert result.page_content == expected_pdf_content.page_content
    assert result.metadata.get("file_name") == expected_pdf_content.metadata.get("file_name")
    assert result.metadata.get("file_id") == expected_pdf_content.metadata.get("file_id")


def test_extract_text_from_pdf_not_valid_pdf(test_document_ingest_service, monkeypatch):
    """Test if extracting data from a non pdf file is handled"""
    with pytest.raises(PDFExtractionError):
        test_document_ingest_service.extract_text_from_pdf(file_content=b'not a pdf file', file_name="file_name",
                                                           file_id="d875d722-be7e-48bb-89f1-d78960224eea",
                                                           workspace_id=workspace_id)
