import logging
import mimetypes
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import ValidationError

from source.enums.file_enums import FileType
from source.exceptions.commons import NotOkServiceResponse
from source.exceptions.custom_exceptions import FileTypeExtractionError
from source.models.enums import RequestMethod
from source.schemas.api_schemas import FileInputSchema
from source.schemas.ingestion_schemas import IngestedFilesCountOutput
from source.schemas.source_schemas import SourceLimitSchema, SourceTypeOutputSchema
from source.schemas.source_schemas import SourceVerificationInput, SourceOutput, SourceDataOutput, \
    SourceVerificationOutput
from source.utils.utils import make_request, parse_metadata_id_object, guess_and_extract_content_type


class SourceService:
    def __init__(self, config: dict) -> None:
        self.config = config

    async def preview_document(self, user_id: str, file_input: FileInputSchema,
                               file_id: str) -> FileResponse | Response | JSONResponse:
        """highlight a file based on content inside of the file and its file_id if it is a pdf file otherwise send the entire document
        for FrontEnd to handle it"""

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
        file_name = parse_metadata_id_object(metadata_object=file_type_response)

        try:
            mime_type, extracted_file_type = guess_and_extract_content_type(file_name=file_name)
        except FileTypeExtractionError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="An error occurred while extracting the file's content type")

        # Non PDF files will be handled in FE, just return the file
        if extracted_file_type != FileType.PDF:
            file_response: FileResponse = await make_request(
                service_url=self.config["FILE_HANDLER_URL"],
                query_params={"user_id": self.config["FILE_HANDLER_USER"], "file_id": str(file_id)},
                uri="/get_file",
                method=RequestMethod.GET,
                headers={"access_api_key": self.config['FILE_HANDLER_API_KEY']}
            )

            # In case fetching the file raises an error
            if isinstance(file_response, NotOkServiceResponse):
                return file_type_response

            return FileResponse(file_response.path, media_type=mime_type,
                                headers={"Content-Disposition": f"attachment; filename={file_name}"})

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

    async def count_files_in_es(self, user_id: str,
                                workspace_id: UUID) -> IngestedFilesCountOutput | NotOkServiceResponse:
        """count files in elastic search"""
        headers = {
            "user-id": user_id,
        }
        files_count_response = await make_request(
            service_url=self.config['SOURCES_SERVICE_URL'],
            uri="/sources/count",
            method=RequestMethod.GET,
            headers=headers,
            query_params=jsonable_encoder({"workspace_id": workspace_id}),

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

    async def get_available_sources_per_type(self, type_id: UUID) -> SourceTypeOutputSchema:
        """
        Get list of available sources per type
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/sources/type",
            method=RequestMethod.GET,
            query_params={"type_id": str(type_id)}
        )

    async def verify_source(self, source_verification_input: SourceVerificationInput) -> SourceVerificationOutput:
        return await make_request(
            service_url=self.config["SOURCES_SERVICE_URL"],
            uri="/sources/verification",
            body=jsonable_encoder(source_verification_input),
            method=RequestMethod.POST,
        )

    async def extract_source_information(self, source: SourceOutput) -> SourceDataOutput:
        return await make_request(
            service_url=self.config["SOURCES_SERVICE_URL"],
            uri="/sources",
            body=jsonable_encoder(source.dict(exclude={"user_id", "metadata"})),
            method=RequestMethod.POST,
        )

    async def update_source_field_mapping(self, source: SourceDataOutput) -> SourceDataOutput:
        return await make_request(
            service_url=self.config["SOURCES_SERVICE_URL"],
            uri="/sources",
            body=jsonable_encoder(source),
            method=RequestMethod.PUT,
        )
