import json
import logging
from typing import AsyncGenerator
from uuid import UUID

import httpx
from aiohttp import ClientSession
from fastapi import HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from loguru import logger
from pydantic import ValidationError

from configuration.config import app_config
from source.exceptions.commons import NotOkServiceResponse
from source.exceptions.custom_exceptions import SchemaError, UserInformationFormatError, ModelConfigError
from source.models.enums import RequestMethod
from source.schemas.answer_schemas import AnswerRatingRequest, AnswerRatingResponse, AnswerUpdatingRequest, \
    VersionedAnswerResponse
from source.schemas.api_schemas import SourceResponse, AnswerOutputSchema, ModelInfoSchema, PromptOutputSchema, \
    QuestionInput, ModelPostInfoSchema, ModelSourcesUpdateSchema, ChatModelsOutputSchema, \
    QuestionLimitOutputSchema
from source.schemas.common import QueryDepth
from source.schemas.conversation_schemas import QuestionInputSchema, AnswerSchema
from source.schemas.source_schemas import SourceSchema, WebSourceSchema, SourceLimitSchema
from source.schemas.streaming_answer_schema import ModelStreamingErrorResponse
from source.schemas.workspace_schemas import WorkspaceTypeModel, WorkspaceTypesEnum
from source.services.keycloak_service import KeycloakService
from source.utils.utils import make_request


class ChatService:
    def __init__(self, config: dict, keycloak_service: KeycloakService) -> None:
        self.config = config
        self.__keycloak_service = keycloak_service

    async def add_question(self, user_id: str, conversation_id: str, question: QuestionInputSchema, skip_doc: bool,
                           skip_web: bool, workspace_id: UUID,
                           use_classification: bool = True) -> QuestionLimitOutputSchema | NotOkServiceResponse:
        headers = {
            "user-id": user_id,
            "workspace-id": str(workspace_id)
        }
        params = {
            'conversation-id': conversation_id,
            'skip_doc': json.dumps(skip_doc),
            'skip_web': json.dumps(skip_web),
            'use_classification': json.dumps(use_classification)
        }
        question_response = await make_request(
            service_url=self.config.get("CONVERSATION_SERVICE_URL"),
            uri="/conversations/question",
            method=RequestMethod.POST,
            body=question.dict(),
            query_params=params,
            headers=headers
        )

        if isinstance(question_response, NotOkServiceResponse):
            return question_response

        try:
            return QuestionLimitOutputSchema(**question_response)
        except ValidationError as error:
            logging.error(f"Failed to create Question: {error}")
            raise UserInformationFormatError from error

    async def get_answer(self, user_id: str, model_code: str, question_id: str) -> AnswerOutputSchema:
        headers = {
            "user-id": user_id,
            "model-code": model_code
        }

        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/chat/answer/{question_id}",
            method=RequestMethod.GET,
            headers=headers
        )

    async def get_chat_models(self) -> list[ModelInfoSchema]:
        """Get available models for chat"""
        return await make_request(
            service_url=self.config.get("CONVERSATION_SERVICE_URL"),
            uri=self.config.get("MODELS_ENDPOINT"),
            method=RequestMethod.GET,
        )

    async def get_available_chat_models_by_workspace_id(self, workspace_id: UUID) -> ChatModelsOutputSchema:
        """Get available models for chat by workspace_id"""
        models_endpoint = self.config.get("MODELS_ENDPOINT")
        return await make_request(
            service_url=self.config.get("CONVERSATION_SERVICE_URL"),
            uri=f"{models_endpoint}/workspaces?workspace_id={workspace_id}",
            method=RequestMethod.GET,
        )

    async def add_model(self, model_info_input: ModelPostInfoSchema) -> ModelInfoSchema:
        """Add a new model with a unique model code"""
        return await make_request(
            service_url=self.config.get("CONVERSATION_SERVICE_URL"),
            uri=self.config.get("MODELS_ENDPOINT"),
            method=RequestMethod.POST,
            body=model_info_input.dict()
        )

    async def patch_model(self, model_info_input: ModelSourcesUpdateSchema) -> ModelInfoSchema:
        """Patch an existing model to alter the max web and max local attributes"""
        return await make_request(
            service_url=self.config.get("CONVERSATION_SERVICE_URL"),
            uri=self.config.get("MODELS_ENDPOINT"),
            method=RequestMethod.PATCH,
            body=model_info_input.dict()

        )

    async def get_model_config_per_model_code(self, model_code: str) -> SourceLimitSchema:
        model_info_url = self.config.get("MODELS_ENDPOINT")
        source_config = await make_request(
            service_url=self.config.get("CONVERSATION_SERVICE_URL"),
            uri=f"{model_info_url}/{model_code}",
            method=RequestMethod.GET,
            query_params={"model_code": model_code},
        )
        try:
            return SourceLimitSchema(modelCode=source_config.get("code"),
                                     maxLocal=source_config.get("max_doc"),
                                     maxWeb=source_config.get("max_web"))
        except ValidationError as error:
            logging.error(error)
            raise ModelConfigError(detail="Could not extract the sources configuration")

    async def get_web_source(self, user_id: str, question: QuestionInput, model_code: str,
                             web_sources_count: int | None) -> SourceResponse:
        """Validate if the count of web sources is correct, fetch them from the sources service then save them into
        conversation service before returning them"""

        if web_sources_count is None:
            sources_config = await self.get_model_config_per_model_code(model_code=model_code)
            web_sources_count = sources_config.max_web

        headers = {
            "user-id": user_id,
        }
        # get web sources
        web_sources = await make_request(
            service_url=self.config["SOURCES_SERVICE_URL"],
            uri="/sources/web",
            method=RequestMethod.POST,
            body=jsonable_encoder({"content": question.content}),
            query_params=jsonable_encoder({"web_sources_count": web_sources_count}),
            headers=headers
        )
        if isinstance(web_sources, NotOkServiceResponse):
            raise HTTPException(status_code=500, detail="failed to get web sources")
        if web_sources_data := web_sources.get("data"):
            # save web sources in db if web_sources_data is not an empty list
            web_sources_response = await make_request(
                service_url=self.config["CONVERSATION_SERVICE_URL"],
                uri="/conversations/web-sources",
                method=RequestMethod.POST,
                query_params=jsonable_encoder({"question_id": question.id}),
                body={
                    "web_sources": web_sources_data
                },
                headers=headers
            )
            if isinstance(web_sources_response, NotOkServiceResponse):
                raise HTTPException(status_code=500, detail="failed to get web sources")
            try:
                return SourceResponse(data=[WebSourceSchema(**data) for data in web_sources_response], detail="success")
            except ValidationError as error:
                logger.error(error)
                raise SchemaError
        return web_sources

    async def get_source_docs(self, user_id: str, question: QuestionInput, model_code: str,
                              local_sources_count: int | None, workspace_id: UUID) -> SourceResponse:
        """Validate if the count of local sources is correct, fetch them from the sources service then save them into
        conversation service before returning them"""

        if local_sources_count is None:
            sources_config = await self.get_model_config_per_model_code(model_code=model_code)
            local_sources_count = sources_config.max_local

        headers = {
            "user-id": user_id,
        }
        # get sources documents
        similar_docs_response = await make_request(
            service_url=self.config["SOURCES_SERVICE_URL"],
            uri="/sources/similar",
            method=RequestMethod.POST,
            body=jsonable_encoder({"content": question.content}),
            query_params=jsonable_encoder({"local_sources_count": local_sources_count, "workspace_id": workspace_id}),
            headers=headers
        )
        if isinstance(similar_docs_response, NotOkServiceResponse):
            raise HTTPException(status_code=500, detail="failed to get sources documents")
        if similar_docs_data := similar_docs_response.get("data"):
            # save sources documents in db if similar_docs_data is not an empty list
            sources_response = await make_request(
                service_url=self.config["CONVERSATION_SERVICE_URL"],
                uri="/conversations/sources",
                method=RequestMethod.POST,
                query_params=jsonable_encoder({"question_id": question.id}),
                body={
                    "similar_docs": similar_docs_data
                },
                headers=headers
            )
            if isinstance(sources_response, NotOkServiceResponse):
                raise HTTPException(status_code=500, detail="failed to get sources response")
            try:
                return SourceResponse(data=[SourceSchema(**data) for data in sources_response], detail="success")
            except ValidationError as error:
                logger.error(error)
                raise SchemaError
        return similar_docs_response

    async def create_rating_for_answer(self, user_id, request_body: AnswerRatingRequest) -> AnswerRatingResponse:

        """
        Creates a rating for an answer provided by the conversation service.

        Args:
            user_id: The user ID for whom the rating is being created.
            request_body (AnswerRatingRequest): The request body containing the rating information.

        Returns:
            Union[Dict[str, Any], None]: The response from the conversation service or None if an error occurs.
        """

        headers = {
            "user-id": user_id
        }

        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri="/chat/answer/rating",
            method=RequestMethod.PUT,
            body=jsonable_encoder(request_body),
            headers=headers,
        )

    async def create_prompt(self, user_id: str, model_code: str, question_id: UUID) -> PromptOutputSchema:
        headers = {
            "user-id": user_id,
            "model-code": model_code
        }
        generated_prompt = await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/chat/prompt/{question_id}",
            method=RequestMethod.GET,
            query_params=jsonable_encoder({"use_web_sources_flag": "true"}),
            headers=headers
        )
        if isinstance(generated_prompt, NotOkServiceResponse):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="failed to get prompt")
        return generated_prompt

    async def update_answer_with_versioning(self, update_answer_request: AnswerUpdatingRequest, answer_id: UUID,
                                            user_id: UUID) \
            -> AnswerSchema | NotOkServiceResponse:
        """
        update an answer with new content through the conversation service, also applies versioning to older content
        """
        headers = {
            "user-id": str(user_id),
        }
        return await make_request(
            service_url=self.config.get("CONVERSATION_SERVICE_URL"),
            uri="/chat/answer",
            method=RequestMethod.PUT,
            headers=headers,
            body={
                "id": str(answer_id),
                "content": update_answer_request.content
            }
        )

    async def get_latest_versioned_answer(self, answer_id: UUID, user_id: UUID) \
            -> VersionedAnswerResponse | NotOkServiceResponse:
        """
        Retrieve the latest older version of a given answer
        """
        headers = {
            "user-id": str(user_id),
        }
        return await make_request(
            service_url=self.config.get("CONVERSATION_SERVICE_URL"),
            uri=f"/chat/answer/{answer_id}/history/latest",
            method=RequestMethod.GET,
            headers=headers,
        )

    # TODO remove this, as we will use the sources stored in conversation service
    async def _extract_config_per_model(self, model_code: str) -> SourceLimitSchema:
        """Extract the model config from the keycloak response"""
        source_configs = await self.__keycloak_service.get_sources_configurations()

        for source_config in source_configs:
            source_config_schema = SourceLimitSchema(**source_config)
            if source_config_schema.model_code == model_code:
                return source_config_schema

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"the provided model code {model_code} has no available sources' configuration")

    async def generate_answer_by_streaming(self, user_id: str, model_code: str, question_id: str, request: Request,
                                           workspace_type: WorkspaceTypesEnum,
                                           workspace_id: str,
                                           query_depth: QueryDepth
                                           ) -> AsyncGenerator:
        """
               Stream the answer to a given text asynchronously.
              Args:
                text (str): The text for which you want to retrieve an answer.
                request (Request): The FastAPI request object to check for disconnection.
                user_id (str): The user identifier.
                model_code (str): The code of the model being used.
                question_id (str): The identifier of the question.
                workspace_type (WorkspaceTypesEnum): The type of workspace being used.
                workspace_id (str): The identifier of the workspace
               Yields:
                   Union[bytes, dict]: The streamed chunks of data or an error dictionary.
        """
        headers = {
            "user-id": user_id,
            "model-code": model_code,
            "workspace-id": workspace_id
        }
        endpoint = f"/chat/answer/{question_id}/sql/stream" if workspace_type == WorkspaceTypesEnum.database else \
            f"/chat/answer/{question_id}/stream"

        query_params = {"queryDepth": query_depth.value} if workspace_type == WorkspaceTypesEnum.database else {}

        async with httpx.AsyncClient() as client:
            async with client.stream('GET', f'{self.config.get("CONVERSATION_SERVICE_URL")}{endpoint}',
                                     headers=headers, params=query_params,
                                     timeout=300) as resp:
                if resp.status_code == status.HTTP_200_OK:
                    async for chunk in resp.aiter_bytes():
                        logger.info(f"chunk {chunk}")
                        if await request.is_disconnected():
                            logger.info("Connection disconnected, end streaming!")
                            break
                        yield chunk
                else:
                    yield str(ModelStreamingErrorResponse(
                        detail=f"Request failed with status code {resp.status_code}"))


    async def get_workspace_type_by_id(self, workspace_id: str) -> WorkspaceTypesEnum:
        """
        Get the workspace type by its id
        Args:
            workspace_id (str): The workspace identifier
        Returns:
            WorkspaceTypesEnum: The workspace type
        Raises:
            HTTPException: If the workspace type does not exist for that id
        """
        workspace_type_dict = await make_request(service_url=self.config.get("CONVERSATION_SERVICE_URL"),
                                                 uri=f"/workspaces/{workspace_id}/type",
                                                 method=RequestMethod.GET)

        try:
            return WorkspaceTypeModel(**workspace_type_dict).name
        except (AttributeError, TypeError) as error:
            logger.error(error)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
