import traceback
from typing import AsyncGenerator
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound
from starlette.requests import Request

from configuration.config import SQLGenerationConfig
from configuration.logging_setup import logger
from source.exceptions.service_exceptions import (DatabaseConnectionError, ConversationFetchDataError,
                                                  ModelRetrievalError, SqlSourceResponseSavingException,
                                                  SQLModelDiscoveryError, ModelServiceConnectionError,
                                                  ChatModelDiscoveryError, SQLExecuteError, QueryExecutionFail,
                                                  UnauthorizedSQLStatement)
from source.exceptions.validation_exceptions import GenericValidationError
from source.helpers.streaming_helpers import LLMStreamer
from source.models.conversations_models import SqlSourceResponse
from source.repositories.conversation_repository import ConversationRepository
from source.repositories.sql_source_repository import SQLSourceRepository
from source.schemas.conversation_schema import QuestionSchema
from source.schemas.sql_llm_schema import SqlSourceResponseDTO, QueryDepth
from source.schemas.streaming_answer_schema import (ModelStreamingErrorResponse, ModelStreamingInProgressResponse,
                                                    ConversationStreamingDoneResponse)
from source.services.conversation_service import ConversationService
from source.services.llm_chains.abstract import LLMChain
from source.services.model_service import ModelService
from source.services.source_service import SourceService
from source.utils.constants import SQL_EXECUTE_ERROR_RESPONSE_FOR_STREAMING_MESSAGE


class SQLQueryChain(LLMChain):
    """
    This chain is responsible for these steps:
    - construct the first prompt for generating sql query
    - request the appropriate model service to get the generated query
    - execute the sql query if required (TODO)
    - save anything related to this task to the SqlSourceResponse Table
    """

    def __init__(self,
                 model_registry_service: ModelService,
                 sql_generation_config: SQLGenerationConfig,
                 conversation_repository: ConversationRepository,
                 sql_source_repository: SQLSourceRepository,
                 source_service: SourceService
                 ):

        self.model_registry_service = model_registry_service
        self.sql_generation_config = sql_generation_config
        self.conversation_repository = conversation_repository
        self.sql_source_repository = sql_source_repository
        self.source_service = source_service

    async def prepare_prompt_arguments(self, workspace_id: UUID) -> str:
        """
        In this chain, we return a dummy DDL data
        """
        source_ddl = await self.source_service.get_source_ddl(workspace_id)
        return source_ddl.metadata

    def construct_prompt(self, user_query: str, context: str) -> str:
        """
        Use this method to construct the final prompt for generating sql query
        """
        return f"""You are a helpful, respectful and honest assistant with a deep knowledge of code 
            and software design. You are an SQL expert. If a question does not make any sense, or is not 
            factually coherent, explain why instead of answering something not correct. 
            If you don't know the answer to a question, please don't share false information.
            Given the following SQL code describing a database creation: {context}. {user_query}. Please add <SQL> 
            before the code and </SQL> after the SQL code.
            """

    async def generate_answer(self, question_id: UUID,
                              workspace_id: UUID,
                              model_code: str | None = None,
                              execute_sql_query: bool = False) -> SqlSourceResponseDTO:
        """
        :str user_query: represents the user query in human readable format used to generate sql command
        """

        try:
            question_object = QuestionSchema.from_orm(self.conversation_repository.get_question_by_id(question_id))
        except (DatabaseConnectionError, ValidationError) as error:
            raise ConversationFetchDataError(
                f'Failed to fetch question data for question_id: {question_id}!'
            ) from error

        # possibly fetch already saved sql ddl data from postgres db or fetch from source service through REST
        context = await self.prepare_prompt_arguments(workspace_id=workspace_id)

        prompt = self.construct_prompt(user_query=question_object.content, context=context)

        model_code = (
                model_code or self.sql_generation_config.DEFAULT_SQL_LLM_MODEL_CODE
        )

        try:  # validate if model service exists
            self.model_registry_service.get_model_info_per_model_code(model_code)
        except (NoResultFound, GenericValidationError, ModelRetrievalError, ChatModelDiscoveryError) as error:
            logger.error(error)
            raise SQLModelDiscoveryError(message=f"Unable to connect to this model {model_code}") from error

        model_response = self.model_registry_service.request_model_service_per_code(
            text=prompt, model_code=model_code
        )

        logger.info(f"model_response : {model_response.response}")
        sql_query = model_response.response.strip().split("<SQL>")[-1].split("</SQL>")[0]
        logger.info(f"sql_query before preprocessing {sql_query}")
        sql_query_preprocessed = sql_query.split("\n\n")[0]
        logger.info(f"sql_query after preprocessing {sql_query_preprocessed}")

        sql_source_orm_object = SqlSourceResponse(
            question_id=question_id,
            query=sql_query
        )
        if execute_sql_query:
            try:
                sql_response = await self.source_service.execute_sql_command(
                    workspace_id=workspace_id,
                    sql_query=sql_query.replace('\n', ' '))
                sql_source_orm_object.result = sql_response.result
            except UnauthorizedSQLStatement as error:
                logger.error(str(error))
                sql_source_orm_object.result = SQL_EXECUTE_ERROR_RESPONSE_FOR_STREAMING_MESSAGE
            except QueryExecutionFail as error:
                logger.error(str(error))
                raise SQLExecuteError from error

        try:
            sql_source_dto = self.sql_source_repository.create_sql_source_response(sql_source_orm_object)
            sql_source_dto.model_answer = model_response
            return sql_source_dto
        except DatabaseConnectionError as error:
            logger.error(error)
            raise SqlSourceResponseSavingException from error


class FullSQLChain(LLMChain):
    """
    This class contains the SqlQueryChain.

    It is responsible for:
    - Executing the sql query chain
    - constructing the second prompt of sql result explanation
    - saving and streaming the final response

    """

    def __init__(self, llm_sql_query_chain: SQLQueryChain,
                 streamer_handler: LLMStreamer,
                 model_discovery_service: ModelService,
                 conversation_service: ConversationService
                 ):
        self.llm_sql_query_chain = llm_sql_query_chain
        self.model_discovery_service = model_discovery_service
        self.streamer_handler = streamer_handler
        self.conversation_service = conversation_service

        self.done_callback_handler = self.conversation_service.create_answer

    async def prepare_prompt_arguments(self,
                                       question_id: UUID,
                                       workspace_id: UUID,
                                       sql_model_code: str | None = None,
                                       query_depth: QueryDepth = QueryDepth.EXPLANATION) -> SqlSourceResponseDTO:

        execute_sql_query = query_depth in [QueryDepth.EXPLANATION, QueryDepth.RESULT]
        return await self.llm_sql_query_chain.generate_answer(model_code=sql_model_code,
                                                              question_id=question_id,
                                                              execute_sql_query=execute_sql_query,
                                                              workspace_id=workspace_id)

    def construct_prompt(self, sql_source_response: SqlSourceResponseDTO) -> str:
        """
        This method builds a prompt using a default template for now, that will be configurable in the future.
        :param sql_source_response: Contains the SQL query that was executed and its result.
        :return: A filled prompt to be used to explain the SQL query results.
        """
        return f"""You are an assistant and expert in SQL, data analyst, and a software engineer that explains SQL \
        query results to neophyte people who do not know these technical aspects. Given an SQL query to some database \
        and the returned result by executing it (list of tuples, a scalar or a string), you are going to explain them \
        in plain text. You will then provide your expertise in the form of analytics, statistics, insights and \
        observations whenever possible and pertinent. When answering, do not talk about the format of the results provided.\
        Instead, answer how you would to an end user. For example, do not mentions things like "tuple" and other programming-related\
        keyword. Simply reformulate the result of the SQL result execution in a brief and efficient way.
        If you cannot explain the results or if they seem too convoluted, simply say you cannot explain and return the \
        result as is.Here is the executed query: {sql_source_response.query}. And here is the obtained result: \
        {sql_source_response.result}."""

    def _resolve_streaming_done_response(self,
                                         query_depth: QueryDepth,
                                         sql_source_response: SqlSourceResponseDTO,
                                         question_id: UUID
                                         ):
        """
        Used to return one in progress chunk when query_depth is command or execute not explanation
        """

        if query_depth in [QueryDepth.RESULT, QueryDepth.EXPLANATION]:
            sql_source_response.model_answer.response += f"\n{sql_source_response.result}"

        answer_object = self.conversation_service.create_answer(question_id,
                                                                sql_source_response.model_answer)

        return ModelStreamingInProgressResponse(
            data=answer_object.content)

    async def generate_answer(self, request: Request,
                              question_id: UUID,
                              workspace_id: UUID,
                              query_depth: QueryDepth,
                              chat_model_code: str | None = None,
                              ) -> AsyncGenerator:
        """
        This is the end-to-end workflow for sql chain
        Resolves to in progress chunk containing the generated sql query and optionally its result
        """
        # in this case let the default sql model code be used, do not pass this model_code
        try:
            logger.warning(query_depth)
            sql_source_response = await self.prepare_prompt_arguments(question_id=question_id, query_depth=query_depth,
                                                                      workspace_id=workspace_id)

            if query_depth in [QueryDepth.COMMAND, QueryDepth.RESULT]:
                yield str(self._resolve_streaming_done_response(
                    query_depth=query_depth,
                    sql_source_response=sql_source_response,
                    question_id=question_id
                )
                )
                yield str(
                    ConversationStreamingDoneResponse(detail="Success!", metadata=sql_source_response.dict())
                )
                return

            prompt = self.construct_prompt(sql_source_response)

            response = self.model_discovery_service.request_model_service_per_code_by_streaming(
                model_code=chat_model_code,
                text=prompt)
        except (ConversationFetchDataError,
                ModelServiceConnectionError,
                SQLModelDiscoveryError,
                DatabaseConnectionError,
                SQLExecuteError) as error:

            logger.error(error)
            yield str(ModelStreamingErrorResponse(
                detail="An unexpected Error while requesting the model!",
                metadata={
                    "error": str(error),
                    "error_type": str(type(error)),
                    "error_message": error.message,
                    "traceback": traceback.format_exc()
                }
            ))
            return

        async for chunk in self.streamer_handler.stream_llm_response(response=response,
                                                                     request=request,
                                                                     model_code=chat_model_code,
                                                                     question_id=question_id,
                                                                     final_response_metadata=sql_source_response.dict()
                                                                     ):
            yield chunk
