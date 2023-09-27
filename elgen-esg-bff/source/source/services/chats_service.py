import json
import logging
from typing import AsyncGenerator
from uuid import UUID

import requests
from fastapi import HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from loguru import logger
from pydantic import ValidationError

from source.exceptions.commons import NotOkServiceResponse
from source.exceptions.custom_exceptions import SchemaError, UserInformationFormatError
from source.models.enums import RequestMethod
from source.schemas.answer_schemas import AnswerRatingRequest, AnswerRatingResponse, AnswerUpdatingRequest, \
    VersionedAnswerResponse
from source.schemas.api_schemas import SourceResponse, AnswerOutputSchema, ModelInfoSchema, PromptOutputSchema, \
    QuestionSchema, QuestionInput, ModelPostInfoSchema, ModelSourcesUpdateSchema
from source.schemas.conversation_schemas import QuestionInputSchema, AnswerSchema
from source.schemas.source_documents_schemas import SourceSchema, WebSourceSchema, SourceLimitSchema
from source.schemas.streaming_answer_schema import ModelStreamingErrorResponse
from source.services.keycloak_service import KeycloakService
from source.utils.utils import make_request


class ChatService:
    def __init__(self, config: dict, keycloak_service: KeycloakService) -> None:
        self.config = config
        self.__keycloak_service = keycloak_service

    async def add_question(self, user_id: str, conversation_id: str, question: QuestionInputSchema, skip_doc: bool,
                           skip_web: bool) -> QuestionSchema | NotOkServiceResponse:
        headers = {
            "user-id": user_id
        }
        params = {
            'conversation-id': conversation_id,
            'skip_doc': json.dumps(skip_doc),
            'skip_web': json.dumps(skip_web)
        }
        question_response = await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri="/conversations/question",
            method=RequestMethod.POST,
            body=question.dict(),
            query_params=params,
            headers=headers
        )

        if isinstance(question_response, NotOkServiceResponse):
            return question_response

        try:
            return QuestionSchema(**question_response)
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

    async def get_web_source(self, user_id: str, question: QuestionInput, model_code: str,
                             web_sources_count: int | None) -> SourceResponse:
        """Validate if the count of web sources is correct, fetch them from the sources service then save them into
        conversation service before returning them"""

        if web_sources_count is None:
            sources_config = await self._extract_config_per_model(model_code=model_code)
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
            raise HTTPException(status_code=500, detail="failed to get sources documents")
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
                raise HTTPException(status_code=500, detail="failed to get sources response")
            try:
                return SourceResponse(data=[WebSourceSchema(**data) for data in web_sources_response], detail="success")
            except ValidationError as error:
                logger.error(error)
                raise SchemaError
        return web_sources

    async def get_source_docs(self, user_id: str, question: QuestionInput, model_code: str,
                              local_sources_count: int | None) -> SourceResponse:
        """Validate if the count of local sources is correct, fetch them from the sources service then save them into
        conversation service before returning them"""

        if local_sources_count is None:
            sources_config = await self._extract_config_per_model(model_code=model_code)
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
            query_params=jsonable_encoder({"local_sources_count": local_sources_count}),
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

    async def _extract_config_per_model(self, model_code: str) -> SourceLimitSchema:
        """Extract the model config from the keycloak response"""
        source_configs = await self.__keycloak_service.get_sources_configurations()

        for source_config in source_configs:
            source_config_schema = SourceLimitSchema(**source_config)
            if source_config_schema.model_code == model_code:
                return source_config_schema

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"the provided model code {model_code} has no available sources' configuration")

    async def generate_answer_by_streaming(self, text: str, user_id: str, model_code: str,
                                           question_id: str, request: Request) -> AsyncGenerator:
        """
               Stream the answer to a given text asynchronously.
              Args:
                text (str): The text for which you want to retrieve an answer.
                request (Request): The FastAPI request object to check for disconnection.
                user_id (str): The user identifier.
                model_code (str): The code of the model being used.
                question_id (str): The identifier of the question.
               Yields:
                   Union[bytes, dict]: The streamed chunks of data or an error dictionary.
        """
        headers = {
            "user-id": user_id,
            "model-code": model_code
        }

        response = requests.get(f'{self.config.get("CONVERSATION_SERVICE_URL")}/chat/answer/{question_id}/stream',
                                headers=headers, json={"prompt": text}, stream=True)

        if response.status_code == status.HTTP_200_OK:
            for chunk in response.iter_content(chunk_size=self.config.get('RESPONSE_CHUNK_SIZE')):
                if await request.is_disconnected():
                    logger.info("Connection disconnected, end streaming!")
                    break
                yield chunk
        else:
            yield str(ModelStreamingErrorResponse(
                detail=f"Request failed with status code {response.status_code}"))
            return
