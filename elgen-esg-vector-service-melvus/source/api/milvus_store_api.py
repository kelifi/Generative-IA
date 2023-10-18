from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Body, Depends
from fastapi import HTTPException, status
from loguru import logger

from configuration.injection import DependencyContainer
from source.exceptions.service_exceptions import EmptyMilvusCollection, ExistenceCheckError, DataAlreadyInMilvusError
from source.schema.requests import StoreDocumentsRequest, GetSimilarDocumentsRequest, SimilarDocumentsOutput
from source.schema.response import DocumentCountResult
from source.services.milvus_service import MilvusService

milvus_store_router = APIRouter(prefix="/milvus")


@milvus_store_router.post("/store-data", response_model=DocumentCountResult)
@inject
def store_documents(
        milvus_service: MilvusService = Depends(
            Provide[DependencyContainer.milvus_service]
        ),
        request_data: StoreDocumentsRequest = Body(...),

):
    try:
        return DocumentCountResult(count=milvus_service.store_documents(request_data))
    except ExistenceCheckError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error.detail)
    except DataAlreadyInMilvusError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.detail)


@milvus_store_router.post("/similar-docs")
@inject
def get_similar_documents(
        request_data: GetSimilarDocumentsRequest,
        milvus_service: MilvusService = Depends(
            Provide[DependencyContainer.milvus_service]
        )

) -> SimilarDocumentsOutput:
    try:
        return milvus_service.get_similar_documents(query=request_data.query, n_results=request_data.n_results)
    except EmptyMilvusCollection as error:
        logger.warning("No similar documents returned!")
        return SimilarDocumentsOutput(data=[], detail=error.detail)


@milvus_store_router.post("/count", response_model=DocumentCountResult)
@inject
def get_documents_count(
        milvus_service: MilvusService = Depends(
            Provide[DependencyContainer.milvus_service])):
    return DocumentCountResult(count=milvus_service.get_total_documents_count())
