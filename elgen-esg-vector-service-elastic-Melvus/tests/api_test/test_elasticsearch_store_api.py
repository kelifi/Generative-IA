from unittest import mock

import pytest

from main import app
from source.schema.requests import SimilarDocumentsOutput
from source.schema.schemas import ESDocumentCountSchema
from source.services.elasticsearch_service import EmbeddingIndexerService
from tests.conftest import test_client
from tests.test_data import MocksConstants

service_mock = mock.Mock(spec=EmbeddingIndexerService)


@pytest.mark.asyncio
async def test_get_similar_documents(test_client, monkeypatch):
    """Test getting of similar documents"""
    service_mock.get_similar_documents.return_value = SimilarDocumentsOutput(**MocksConstants.dummy_similar_docs)
    with app.container.es_service.override(service_mock):
        result = test_client.post(
            url=f"/es/similar-docs",
            json=MocksConstants.dummy_similar_docs_request
        )
        assert result.status_code == 200
        assert result.json() == MocksConstants.dummy_similar_docs


async def test_count_es_documents(test_client, monkeypatch):
    """Test getting of similar documents"""
    service_mock.count_ingested_documents.return_value = ESDocumentCountSchema(**MocksConstants.dummy_nb_documents)
    with app.container.es_service.override(service_mock):
        result = test_client.get(
            url=f"/es/count",
            query={"workspace_id" : MocksConstants.workspace_id}
        )
        assert result.status_code == 200
        assert result.json() == MocksConstants.dummy_nb_documents
