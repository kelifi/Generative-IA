from typing import List, Optional
import json
import logging
from json import JSONDecodeError
from typing import List, Optional, AsyncGenerator
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.requests import Request
from pydantic import ValidationError

from configuration.config import SummarizationConfig, StreamingResponseConfig
from configuration.logging_setup import logger
from source.exceptions.service_exceptions import ModelServiceConnectionError, DataLayerError, ChatServiceError, \
    ConversationFetchDataError, \
    ConversationNotFoundError, SourceDocumentsFetchDataError, ChatIncompleteDataError, ChatAnswerCreationError, \
    AnswerNotFoundException, AnswerNotFoundError, VersionedAnswerNotFoundException, ModelServiceParsingError
from source.repositories.answer_repository import AnswerRepository
from source.schemas.answer_schema import AnswerRatingResponse, VersionedAnswerResponse
from source.schemas.chat_schema import PromptSchema
from source.schemas.conversation_schema import ChatSchema, SourceSchema, AnswerOutputSchema, WebSourceSchema, \
    AnswerSchema
from source.schemas.models_schema import ModelServiceAnswer
from source.schemas.streaming_answer_schema import ModelStreamingErrorResponse, StreamingResponseStatus, \
    ModelStreamingInProgressResponse, ModelStreamingDoneResponse, ConversationStreamingDoneResponse
from source.services.conversation_service import ConversationService
from source.services.model_service import ModelService


class ChatService:
    """
    Service class for generating answers based on chat history and source documents.
    """

    def __init__(self,
                 conversation_service: ConversationService,
                 answer_repository: AnswerRepository,
                 model_discovery_service: ModelService,
                 summarization_config: SummarizationConfig,
                 streaming_response_config: StreamingResponseConfig
                 ):
        """
        Initialize the ChatService.

        Args:
            conversation_service (ConversationService): The conversation service to use.
        """
        self.conversation_service = conversation_service
        self._answer_repository = answer_repository
        self._headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.model_discovery_service = model_discovery_service
        self.summarization_config = summarization_config
        self.streaming_response_config = streaming_response_config

    def prepare_prompt_arguments(self, question_id: UUID, model_code: str,
                                 use_web_sources_flag: bool = True) -> \
            tuple[str, ChatSchema, List[SourceSchema], list[WebSourceSchema], list[str] | None]:
        """Using the question id, we fetch the chat_history, source_documents and question, we then set the web sources
        and return all of them

        Args:
            question_id (UUID): The ID of the question.
            model_code (str): The model code
            use_web_sources_flag: A flag indicating if we want to use online sources or not

        Returns:
            data to pass to prompt:tuple[str, ChatSchema, List[SourceSchema], list[WebSourceSchema], list[str] | None]"""
        try:
            question = self.conversation_service.get_question_by_id(question_id).content
            chat_history = self.conversation_service.get_conversation_by_question_id(question_id)
        except ConversationFetchDataError:
            raise ChatIncompleteDataError('Incomplete chat history data')
        except ConversationNotFoundError:
            raise ChatIncompleteDataError(f'historical data not found for question_id: {question_id}')
        try:
            source_documents = self.conversation_service.get_source_documents(question_id)
        except SourceDocumentsFetchDataError:
            raise ChatIncompleteDataError('Internal error when fetching source docs')

        # Collect online sources and summarize them using an LLM model
        if use_web_sources_flag:
            try:
                web_sources = self.conversation_service.get_web_sources_by_question_id(question_id)
            except SourceDocumentsFetchDataError:
                raise ChatIncompleteDataError('Internal error when fetching web source docs')
            summarized_paragraphs = '\n'.join(
                [self.model_discovery_service.request_model_service_per_code(model_code=model_code,
                                                                             text=self._generate_summarization_prompt(
                                                                                 text_to_summarize=web_source.paragraphs)
                                                                             ).response for
                 web_source in web_sources])
        else:
            web_sources = []
            summarized_paragraphs = None

        return question, chat_history, source_documents, web_sources, summarized_paragraphs

    def generate_answer(self, question_id: UUID, model_code: str,
                        use_web_sources_flag: bool = True) -> AnswerOutputSchema:
        """
        Generate an answer for a question using chat history and source documents.

        Args:
            question_id (UUID): The ID of the question.
            model_code (str): The used model code
            use_web_sources_flag: A flag indicating if we want to use online sources or not

        Returns:
            str: The generated answer.
        """
        try:
            question, chat_history, source_documents, web_sources, summarized_paragraphs = self.prepare_prompt_arguments(
                question_id=question_id, model_code=model_code, use_web_sources_flag=use_web_sources_flag)

            prompt_text = self._generate_prompt(chat_history=chat_history, source_documents=source_documents,
                                                question=question,
                                                web_source_summarized_paragraph=summarized_paragraphs)

            answer = self.model_discovery_service.request_model_service_per_code(model_code=model_code,
                                                                                 text=prompt_text)

            answer_object = self.conversation_service.create_answer(question_id, answer)
        except (ModelServiceConnectionError, ConversationFetchDataError, ModelServiceParsingError) as error:
            logger.error(error)
            raise ChatAnswerCreationError('Failed to create answer!') from error

        try:
            return AnswerOutputSchema(id=question_id, answer=answer_object)
        except ValidationError as error:
            logger.error(f"Verify the schema between services: {error}")
            raise ChatAnswerCreationError(
                'Unexpected error while generating the answer!'
            ) from error

    @staticmethod
    def _generate_prompt(chat_history: ChatSchema, source_documents: List[SourceSchema],
                         web_source_summarized_paragraph: Optional[str], question: str) -> str:
        """
        Generate the prompt text for the model based on chat history, source documents, and the question.

        Args:
            chat_history (ChatSchema): The chat history.
            source_documents (List[SourceSchema]): The source documents.
            web_source_summarized_paragraph (Optional[str]): the summarized paragraphs from the source documents
            question (str): The question.

        Returns:
            str: The generated prompt text.
        """
        source_documents_string = "\n".join([source_document.content for source_document in source_documents])

        prompt_template = f"""Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

                {source_documents_string}

                {web_source_summarized_paragraph if web_source_summarized_paragraph else ''}

                Question: {question}
                """

        return prompt_template

    def _generate_summarization_prompt(self, text_to_summarize: str) -> str:
        """Generate the prompt to summarize"""

        return f"""Summarize the following text in {self.summarization_config.NUM_LINES} lines.
                    Text: {text_to_summarize}"""

    def construct_full_prompt(self, question_id: UUID, model_code: str,
                              use_web_sources_flag: bool) -> PromptSchema:
        """
        Get the data needed and generate a full prompt
        Args:
            question_id (UUID): The ID of the question.
            model_code (str): the model code
            use_web_sources_flag: A flag indicating if we want to use online sources or not

        Returns:
            str: The generated answer.
        """
        question, chat_history, source_documents, _, summarized_paragraphs = self.prepare_prompt_arguments(
            question_id=question_id, model_code=model_code, use_web_sources_flag=use_web_sources_flag)
        generated_prompt = self._generate_prompt(chat_history=chat_history, question=question,
                                                 source_documents=source_documents,
                                                 web_source_summarized_paragraph=summarized_paragraphs)
        logger.info(f"Generated prompt: {generated_prompt}")
        return PromptSchema(prompt=generated_prompt)

    def set_rating_for_answer(self, answer_id: UUID, rating: str) -> AnswerRatingResponse:
        """
        Update an answer with a given rating value
        """
        try:
            if self._answer_repository.update_rating_for_answer(
                    answer_id=answer_id, rating=rating
            ):
                # if result is 1, updated
                return AnswerRatingResponse()

            # if result is 0, it means answer does not exist
            raise HTTPException(detail="Answer does not exist", status_code=status.HTTP_404_NOT_FOUND)
        except DataLayerError as error:
            raise ChatServiceError(message="Unexpected Error!") from error

    def update_answer_with_versioning(self, answer_id: UUID, content: str) -> AnswerSchema:
        """
        Update the content of a given answer and saves the old content as a new entry in versioned answer table
        """
        try:
            result = self._answer_repository.update_answer_with_versioning(answer_id=answer_id, content=content)

            return AnswerSchema.from_orm(result)
        except AnswerNotFoundException as exception:
            logger.error(exception)
            raise AnswerNotFoundError from exception
        except (DataLayerError, SourceDocumentsFetchDataError) as error:
            raise ChatServiceError(message=error.message) from error

    def get_last_versioned_answer(self, answer_id: UUID) -> VersionedAnswerResponse:
        """
        Given an answer, returns the latest older version
        """
        try:
            if result := self._answer_repository.get_latest_versioned_answer(
                    answer_id=answer_id
            ):
                return VersionedAnswerResponse.from_orm(result)
            raise VersionedAnswerNotFoundException(message="This answer has no older versions yet")

        except DataLayerError as error:
            raise ChatServiceError(message=error.message) from error

    async def generate_answer_by_streaming(self, request: Request, question_id: UUID, model_code: str,
                                           use_web_sources_flag: bool = True) -> AsyncGenerator:
        """
        Generate an answer for a question using chat history and source documents asynchronously

        Args:
            question_id (UUID): The ID of the question.
            model_code (str): The used model code
            use_web_sources_flag: A flag indicating if we want to use online sources or not

        Returns:
            str: The generated answer.
        """
        try:

            question, chat_history, source_documents, web_sources, summarized_paragraphs = self.prepare_prompt_arguments(
                question_id=question_id, model_code=model_code, use_web_sources_flag=use_web_sources_flag)

            prompt_text = self._generate_prompt(chat_history=chat_history, source_documents=source_documents,
                                                question=question,
                                                web_source_summarized_paragraph=summarized_paragraphs)

            response = self.model_discovery_service.request_model_service_per_code_by_streaming(model_code=model_code,
                                                                                                text=prompt_text)

        except (ModelServiceConnectionError, ConversationFetchDataError, ModelServiceParsingError) as error:
            logger.error(error)
            yield str(ModelStreamingErrorResponse(
                detail="Unable to stream response!"
            ))
            return

        counter = 0
        generated_tokens = []

        if await request.is_disconnected():
            logger.info("Connection disconnected, end streaming!")
            return

        try:
            for chunk in response.iter_content(chunk_size=self.streaming_response_config.STREAMING_CHUNK_SIZE):
                # Process the chunk here (e.g., write it to a file, analyze it, etc.)
                # Example: file.write(chunk)
                counter += 1
                is_disconnected = await request.is_disconnected()
                logger.info(f"Is disconnected {is_disconnected} : {counter}")
                if await request.is_disconnected():
                    logger.info("Connection disconnected, end streaming!")
                    break
                logger.info(f"chunk {chunk}")

                parsed_chunk = json.loads(chunk)

                if parsed_chunk.get("status") == StreamingResponseStatus.IN_PROGRESS:
                    generated_tokens.append(ModelStreamingInProgressResponse(**parsed_chunk).data)
                    yield chunk

                elif parsed_chunk.get("status") == StreamingResponseStatus.DONE:
                    model_answer_object = ModelServiceAnswer(**parsed_chunk.get('data'), model_code=model_code)
                    final_chunk_response = ModelStreamingDoneResponse(data=model_answer_object)
                    answer_object = self.conversation_service.create_answer(question_id, final_chunk_response.data)
                    yield str(
                        ConversationStreamingDoneResponse(data=AnswerOutputSchema(id=str(question_id),
                                                                                  answer=answer_object),
                                                          detail="Success!"))
                    return

                elif parsed_chunk.get("status") == StreamingResponseStatus.ERROR:
                    error_response = ModelStreamingErrorResponse(**parsed_chunk)
                    logger.error(error_response.detail)
                    yield str(error_response)
                    return
                else:
                    logger.error("Streaming response does not have status field, check schema!")
                    yield str(ModelStreamingErrorResponse(
                        detail="Unable to stream response!"
                    ))
                    return
        except (ValidationError, JSONDecodeError) as error:
            logger.error(error)
            yield str(ModelStreamingErrorResponse(
                detail="An unexpected Error occured while parsing response!"
            ))
            return
