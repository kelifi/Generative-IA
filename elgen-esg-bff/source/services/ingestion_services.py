from uuid import UUID

from fastapi import HTTPException, status, UploadFile
from fastapi.encoders import jsonable_encoder

from configuration.config import BFFSettings
from source.exceptions.commons import NotOkServiceResponse
from source.models.enums import RequestMethod
from source.schemas.common import AcknowledgeResponse, AcknowledgeTypes
from source.schemas.ingestion_schemas import IngestedFileOutput
from source.utils.utils import make_request, handle_file_upload


class IngestionService:
    def __init__(self, config: BFFSettings):
        self.config = config

    async def store_documents(self, file: UploadFile, workspace_id: UUID) -> NotOkServiceResponse | IngestedFileOutput:
        """

        @return: The file id from the file handler document
        """

        headers = {"access_api_key": self.config['FILE_HANDLER_API_KEY']}

        file_handler_response = await handle_file_upload(file=file, service_url=self.config['FILE_HANDLER_URL'],
                                                         uri='v2/save_file',
                                                         query_params={"file_path": str(workspace_id)},
                                                         headers=headers,
                                                         method=RequestMethod.POST
                                                         )
        if isinstance(file_handler_response, NotOkServiceResponse):
            return file_handler_response
        file.file.seek(0)
        store_documents_response = await handle_file_upload(file=file,
                                                            service_url=f"http://{self.config['INGEST_SERVICE_HOST']}:{self.config['INGEST_SERVICE_PORT']}",
                                                            uri=f"/ingest/files/{file_handler_response.get('file_id')}",
                                                            method=RequestMethod.POST,
                                                            query_params=jsonable_encoder({"workspace_id": workspace_id}))

        if isinstance(store_documents_response, NotOkServiceResponse):
            return store_documents_response

        return IngestedFileOutput(file_id=file_handler_response.get("file_id"))

    async def delete_ingest_index(self) -> AcknowledgeResponse:
        """

        @return: The acknowledge from ingest service
        """
        delete_ingest_index_response = await make_request(
            service_url=f"http://{self.config['INGEST_SERVICE_HOST']}:{self.config['INGEST_SERVICE_PORT']}",
            uri="/store/es",
            method=RequestMethod.DELETE
        )

        if isinstance(delete_ingest_index_response, NotOkServiceResponse):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="failed delete documents from es")

        return AcknowledgeResponse(acknowledge=AcknowledgeTypes.SUCCESS)
