import json
from json import JSONDecodeError
from typing import AsyncGenerator
from uuid import UUID

from fastapi.requests import Request
from pydantic import ValidationError
from requests import Response

from configuration.config import StreamingResponseConfig
from configuration.logging_setup import logger
from source.schemas.conversation_schema import AnswerOutputSchema
from source.schemas.models_schema import ModelServiceAnswer
from source.schemas.streaming_answer_schema import StreamingResponseStatus, ModelStreamingInProgressResponse, \
    ModelStreamingDoneResponse, ModelStreamingErrorResponse, ConversationStreamingDoneResponse
from source.services.conversation_service import ConversationService


class LLMStreamer:
    """
    Use this helper class to stream from model services
    """

    def __init__(self, streaming_config: StreamingResponseConfig, conversation_service: ConversationService):
        """
        :param streaming_config: contains for now chunk size used to parse streaming response
        : conversation_service: used to save the answer to the database,
        TODO seperate the logic of saving answer outside of conversation_service
        """
        self.streaming_config = streaming_config
        self.conversation_service = conversation_service

    async def stream_llm_response(self,
                                  response: Response,
                                  request: Request,
                                  question_id: UUID,
                                  model_code: str,
                                  final_response_metadata: dict | None = None,
                                  full_prompt: str | None = None
                                  ) -> AsyncGenerator:
        """
        Yield chunk by chunk a streaming REST response as an Async Generator
        :param response: requests.Response object, must be returned from requests.[METHOD] with argument stream=True
        :param request: starlette.requests.Request, used to check for the disconnect of the client
        :param question_id:
        :param model_code: code for model service
        :param final_response_metadata: optional metadata to be included in the Done Chunk

        There are three types of chunks: InProgress, Done and Error.
        Use this method inside another method:
        >>> async for chunk in llm_streamer.stream_llm_response(...):
        >>>     yield chunk

        You can use it directly with FastApi Streaming Response
        """
        if await request.is_disconnected():
            logger.info("Connection disconnected, end streaming!")
            return
        try:
            generated_tokens = []
            for chunk in response.iter_content(chunk_size=self.streaming_config.STREAMING_CHUNK_SIZE):

                if await request.is_disconnected():
                    logger.info("Connection disconnected, end streaming!")
                    break

                parsed_chunk = json.loads(chunk)

                if parsed_chunk.get("status") == StreamingResponseStatus.IN_PROGRESS:
                    generated_tokens.append(ModelStreamingInProgressResponse(**parsed_chunk).data)
                    yield chunk

                elif parsed_chunk.get("status") == StreamingResponseStatus.DONE:
                    model_answer_object = ModelServiceAnswer(**parsed_chunk.get('data'), model_code=model_code,
                                                             prompt=full_prompt)
                    final_chunk_response = ModelStreamingDoneResponse(data=model_answer_object)
                    answer_object = self.conversation_service.create_answer(question_id, final_chunk_response.data)
                    yield str(
                        ConversationStreamingDoneResponse(data=AnswerOutputSchema(id=str(question_id),
                                                                                  answer=answer_object),
                                                          detail="Success!", metadata=final_response_metadata))
                    return

                elif parsed_chunk.get("status") == StreamingResponseStatus.ERROR:
                    error_response = ModelStreamingErrorResponse(**parsed_chunk)
                    logger.error(error_response.detail)
                    yield str(error_response)
                    return
                else:
                    logger.error("Streaming response does not have status field, check schema!")
                    yield str(ModelStreamingErrorResponse(
                        detail="Unable to stream response!",
                        metadata={"error": "Streaming response does not have status field, check schema!"}
                    ))
                    return
        except (ValidationError, JSONDecodeError) as error:
            logger.error(error)
            yield str(ModelStreamingErrorResponse(
                detail="An unexpected Error occured while parsing response!"
            ))
            return
