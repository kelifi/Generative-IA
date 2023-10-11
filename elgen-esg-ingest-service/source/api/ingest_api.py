from uuid import UUID

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, HTTPException, status
from fastapi import UploadFile, File, Depends, Path, Query

from configuration.injection import DependencyContainer
from source.exceptions.service_exceptions import VectorApiError, CheckError, \
    FileAlreadyIngestedError, IngestionDeletionError, FileIngestionError, TextRetrievalError, SchemaValidationError, \
    PDFExtractionError
from source.schema.elastic_search_schemas import IngestionDelSchema
from source.schema.response_schemas import GenericResponse
from source.services.document_ingestion_service import DocumentsIngestionService

ingest_router = APIRouter(prefix="/ingest")


@ingest_router.post("/files/{file_id}", response_model=GenericResponse,
                    summary="Ingest a file into elastic search, chunk it and send it to the vector service")
@inject
async def store_file_documents(
        file: UploadFile = File(..., description="Uploaded file, should be PDF for now"),
        file_id: UUID = Path(..., description="The common file handler ID of the file"),
        workspace_id: UUID = Query(..., description="Workspace Id"),
        documents_ingestion_service: DocumentsIngestionService = Depends(
            Provide[DependencyContainer.documents_ingestion_service])
):
    try:
        file_content = await file.read()
        file_name = file.filename
        await documents_ingestion_service.ingest_into_es_and_vector(file_content=file_content, file_name=file_name,
                                                                    file_id=str(file_id),
                                                                    workspace_id=str(workspace_id))
        return GenericResponse(detail="File was ingested, chunked and sent to vector service")

    except (VectorApiError, CheckError, FileIngestionError, TextRetrievalError, SchemaValidationError) as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error.detail)
    except FileAlreadyIngestedError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.detail)

    except PDFExtractionError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.detail)


@ingest_router.delete("/es", description="delete the created ingestion for the index in Elastic Search",
                      response_model=IngestionDelSchema, summary="Delete the ingestion index")
@inject
async def delete_ingest_index(documents_ingestion_service: DocumentsIngestionService = Depends(
    Provide[DependencyContainer.documents_ingestion_service])):
    try:
        return await documents_ingestion_service.delete_ingest_index()
    except IngestionDeletionError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error.detail)
