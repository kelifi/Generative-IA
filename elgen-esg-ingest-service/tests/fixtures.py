import pytest
from fastapi.testclient import TestClient

from configuration.config import TextProcessingConfig, DocumentsConfig, ElasticSearchConfig, VectorStoreApiConfig, \
    AppConfig
from main import app
from source.services.document_ingestion_service import DocumentsIngestionService
from source.services.pdf_extractor.pdf_extractor import PDFExtractor


@pytest.fixture(scope="module")
def test_client() -> TestClient:
    """A fixture to test the fastapi client"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_document_ingest_service() -> DocumentsIngestionService:
    """A fixture to instantiate DocumentsIngestionService"""
    yield DocumentsIngestionService(elastic_search_config=ElasticSearchConfig(), doc_config=DocumentsConfig(),
                                    text_proc_config=TextProcessingConfig(), vec_api_config=VectorStoreApiConfig(),
                                    app_config=AppConfig(), file_to_text_methods={})


@pytest.fixture(scope="module")
def test_pdf_extractor() -> PDFExtractor:
    """A fixture to instantiate PDFExtractor"""
    yield PDFExtractor()
