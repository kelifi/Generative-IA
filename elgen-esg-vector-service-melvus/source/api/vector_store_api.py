from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Body, Depends, HTTPException

from configuration.injection import DependencyContainer
from source.exceptions.service_exceptions import MaxResultValueException, DBRuntimeError
from source.schema.requests import StoreDocumentsRequest, GetSimilarDocumentsRequest
from source.schema.response import TotalDocumentsCountResponse, SimilarDocumentsResponse, GenericResponse
from source.services.chroma_db_services import ChromaDBVectorService

vector_store_router = APIRouter(prefix="/vectors")


@vector_store_router.post("/store")
@inject
async def store_documents(
        vector_service: ChromaDBVectorService = Depends(
            Provide[DependencyContainer.vector_service]
        ),
        request_data: StoreDocumentsRequest = Body(...),

) -> GenericResponse:
    return await vector_service.store_documents(request_data)


@vector_store_router.post("/similar")
@inject
async def get_similar_documents(
        request_data: GetSimilarDocumentsRequest,
        vector_service: ChromaDBVectorService = Depends(
            Provide[DependencyContainer.vector_service]
        ),

) -> SimilarDocumentsResponse:
    try:
        return await vector_service.get_similar_documents(query=request_data.query, n_result=request_data.n_results)
    except MaxResultValueException as error:
        raise HTTPException(detail=str(error), status_code=400) from error
    except DBRuntimeError as error:
        raise HTTPException(detail="Internal Error!", status_code=500) from error


@vector_store_router.post("/documents/count", response_model=TotalDocumentsCountResponse)
@inject
async def get_documents_count(
        vector_service: ChromaDBVectorService = Depends(
            Provide[DependencyContainer.vector_service]
        ),

) -> TotalDocumentsCountResponse:
    return await vector_service.get_total_documents_count()
