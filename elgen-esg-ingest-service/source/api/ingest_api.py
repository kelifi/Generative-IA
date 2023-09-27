from uuid import UUID

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, UploadFile, File, Depends, Path, HTTPException
from starlette.background import BackgroundTasks

from configuration.injection import DependencyContainer
from source.exceptions.service_exceptions import ElasticSearchError, VectorApiError
from source.services.document_ingestion_service import DocumentsIngestionService
from source.services.ingest_service import ingestion_service

ingest_router = APIRouter(prefix="/ingest")


@ingest_router.post("/store")
async def store_documents(bg_tasks: BackgroundTasks):
    return await ingestion_service.ingest_data(bg_tasks)


@ingest_router.delete("/store/es")
async def delete_ingest_index():
    return await ingestion_service.delete_ingest_index()


@ingest_router.post("/files/{file_id}")
@inject
async def store_file_documents(bg_tasks: BackgroundTasks,
                          file: UploadFile = File(...),
                          file_id: UUID = Path(...),
                          documents_ingetion_service: DocumentsIngestionService = Depends(
                              Provide[DependencyContainer.documents_ingetion_service])
                          ):
    try:
        return await documents_ingetion_service.ingest_file_data(bg_tasks, file, str(file_id))
    except ElasticSearchError:
        raise HTTPException(status_code=500, detail='Failed to ingest data to elasticsearch')
    except VectorApiError:
        raise HTTPException(status_code=500, detail='Failed to ingest data to vector store')
