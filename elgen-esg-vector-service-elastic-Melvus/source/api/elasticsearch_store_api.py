from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Body, Depends, HTTPException, status, Query

from configuration.injection import DependencyContainer
from source.exceptions.service_exceptions import ElasticsearchFetchDataError, ElasticsearchStoreDataError, \
    ServiceOutputValidationError, ElasticSearchCountError
from source.schema.requests import StoreDocumentsRequest, GetSimilarDocumentsRequest, SimilarDocumentsOutput
from source.schema.response import DocumentCountResult
from source.schema.schemas import ESDocumentCountSchema
from source.services.elasticsearch_service import EmbeddingIndexerService

es_store_router = APIRouter(prefix="/es")


@es_store_router.post("/store-data", response_model=DocumentCountResult)
@inject
def store_es_documents(
        service: EmbeddingIndexerService = Depends(
            Provide[DependencyContainer.es_service]
        ),
        documents: StoreDocumentsRequest = Body(...),

) -> DocumentCountResult:
    """

    Args:
        service: The embedding indexer injected service
        documents: The input data to store

    Returns:

    """
    try:
        return service.store_documents(documents)
    except ElasticsearchStoreDataError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error.detail)
    except ServiceOutputValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.detail)


@es_store_router.post("/similar-docs", response_model=SimilarDocumentsOutput)
@inject
def get_similar_documents(
        similarity_query_data: GetSimilarDocumentsRequest,
        service: EmbeddingIndexerService = Depends(
            Provide[DependencyContainer.es_service]
        )

) -> SimilarDocumentsOutput:
    """

    Args:

        service: The embedding indexer injected service
        similarity_query_data: The request data to search for

    Returns:

    """
    try:
        return service.get_similar_documents(query=similarity_query_data.query,
                                             n_results=similarity_query_data.n_results,
                                             workspace_id=similarity_query_data.workspace_id)
    except ElasticsearchFetchDataError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error.detail)
    except ServiceOutputValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.detail)


@es_store_router.get("/count", response_model=ESDocumentCountSchema,
                     description="Count how many files are ingested in Elastic search")
@inject
def count_es_documents_per_workspace(
        workspace_id: str = Query(..., description="workspace id of the user"),
        es_service: EmbeddingIndexerService = Depends(
            Provide[DependencyContainer.es_service]
        )):
    try:
        return es_service.count_ingested_documents(workspace_id)
    except ElasticSearchCountError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An error was encountered while counting the ingested files in elastic search")
