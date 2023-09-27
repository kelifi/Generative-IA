import logging
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError

from source.exceptions.commons import NotOkServiceResponse
from source.models.enums import RequestMethod
from source.schemas.api_schemas import FileInputSchema
from source.schemas.ingestion_schemas import IngestedFilesCountOutput
from source.schemas.source_documents_schemas import SourceLimitSchema
from source.utils.utils import make_request, parse_metadata_id_object


class SourceService:
    def __init__(self, config: dict) -> None:
        self.config = config

    async def preview_document(self, user_id: str, file_input: FileInputSchema,
                               file_id: str) -> FileResponse | JSONResponse:
        """highlight a file based on content inside of the file and its file_id"""
        headers = {
            "user-id": user_id,
        }

        file_query_params = {"file_id": file_id, "user_id": user_id}

        file_type_response = await make_request(
            service_url=self.config["FILE_HANDLER_URL"],
            uri="/metadata_id",
            method=RequestMethod.GET,
            query_params=file_query_params,
            headers={"accept": "*/*", "access_api_key": self.config["FILE_HANDLER_API_KEY"]}
        )

        if isinstance(file_type_response, NotOkServiceResponse):
            return file_type_response
        extracted_file_type, file_name = parse_metadata_id_object(metadata_object=file_type_response)

        response = await make_request(
            service_url=self.config["SOURCES_SERVICE_URL"],
            uri="/sources/preview",
            method=RequestMethod.POST,
            body={**file_input.dict(), **{"file_type": extracted_file_type, "fileId": file_id}},
            headers=headers
        )
        response.headers["Content-Disposition"] = f"attachment; filename={file_name}"

        return response

    async def download_document(self, file_id: UUID) -> FileResponse:
        query_params = {"user_id": self.config["FILE_HANDLER_USER"], "file_id": str(file_id)}
        headers = {"access_api_key": self.config['FILE_HANDLER_API_KEY']}

        return await make_request(
            service_url=self.config["FILE_HANDLER_URL"],
            query_params=query_params,
            uri="/get_file",
            method=RequestMethod.GET,
            headers=headers
        )

    async def count_files_in_es(self, user_id: str) -> IngestedFilesCountOutput | NotOkServiceResponse:
        """count files in elastic search"""
        headers = {
            "user-id": user_id,
        }
        files_count_response = await make_request(
            service_url=self.config['SOURCES_SERVICE_URL'],
            uri="/sources/count",
            method=RequestMethod.GET,
            headers=headers
        )

        if isinstance(files_count_response, NotOkServiceResponse):
            return files_count_response

        file_count = files_count_response.get("count")
        if file_count is None:
            logging.error("file_count was returned as None")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="could not extract count field from source service response")
        try:
            return IngestedFilesCountOutput(count=file_count)
        except ValidationError as error:
            logging.error(error)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="A validation error was encountered while creating the count schema")

    async def get_source_configurations(self) -> list[SourceLimitSchema] | NotOkServiceResponse:
        """get the complete configuration of the sources"""
        sources_configs_response = await make_request(
            service_url=self.config["SOURCES_SERVICE_URL"],
            uri="/sources/configuration",
            method=RequestMethod.GET,
        )

        if isinstance(sources_configs_response, NotOkServiceResponse):
            return sources_configs_response

        return [SourceLimitSchema(**model_source_result) for model_source_result in sources_configs_response]
