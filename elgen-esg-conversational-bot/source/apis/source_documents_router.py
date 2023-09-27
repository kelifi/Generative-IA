from os.path import basename
from pathlib import Path

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse

from configuration.config import app_config
from configuration.injection_container import DependencyContainer as Container
from source.exceptions.api_exception_handler import ElgenAPIException
from source.exceptions.service_exceptions import PostgresRetrievalError, NoDataFound
from source.services.documents_highlighting_service import DocumentHighlightService
from source.utils.common_utils import delete_file

source_document = APIRouter(prefix="/source-documents")


@source_document.get("/download-document/{document_path}")
async def get_source_documents(document_path: str) -> FileResponse:
    """

    @param document_path: The path of the document that will be downloaded
    @return: The file ready to be downloaded
    """
    return FileResponse(Path(app_config.SOURCE_DIRECTORY, basename(document_path)), filename=basename(document_path),
                        media_type="application/pdf", status_code=200)


@source_document.get("/documents-display/{source_document_id}")
@inject
async def get_highlighted_doc(
        background_tasks: BackgroundTasks,
        source_document_id: str,
        service: DocumentHighlightService = Depends(
            Provide[Container.documents_highlight_service])) -> FileResponse:
    """
    @param background_tasks: The task that will be executed after returning the file response in order to delete
                             the temp file
    @param source_document_id: The source document id, that will be looked for in the internal db
    @param service: The service class injected in the router
    @return: An annotated file
    """
    try:
        data = service.get_document_and_text(source_document_id)
    except (PostgresRetrievalError, NoDataFound):
        raise ElgenAPIException(status_code=404,
                                detail=f'''{source_document_id} doesn't exist in the internal resources''')
    try:
        file = service.get_annotated_file(data)
    except FileNotFoundError:
        raise ElgenAPIException(status_code=400,
                                detail=f'''The file is not found/was deleted from source documents directory''')
    if not file:
        raise ElgenAPIException(status_code=400,
                                detail=f'''Unable to highlight the source document {source_document_id} : The text was not found in doc''')
    background_tasks.add_task(delete_file, file)
    return FileResponse(file, filename=f'highlighted_{source_document_id}.pdf', media_type="application/pdf",
                        status_code=200)
