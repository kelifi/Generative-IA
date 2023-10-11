from uuid import UUID

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound

from configuration.config import AppConfig
from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseConnectionError, SourceTypeFetchDataError, \
    WorkspaceTypeNotFound, SourceAddingError, SourceDataFetchError, SourceUpdatingError, QueryExecutionFail, \
    UnauthorizedSQLStatement
from source.exceptions.validation_exceptions import GenericValidationError
from source.repositories.sources_repository import SourceRepository
from source.repositories.workspace_type_repository import WorkspaceTypeRepository
from source.schemas.common import RequestMethod
from source.schemas.source_schema import SourceTypeOutputModel, SourceTypeModel, NewSourceSchema, NewSourceOutput, \
    SourceOutputModel, SourceDDLOutputDTO
from source.schemas.sql_llm_schema import SqlExecuteResponse, SqlExecuteRequest
from source.utils.utils import make_request, is_select_query


class SourceService:
    def __init__(self,
                 source_repository: SourceRepository,
                 workspace_type_repository: WorkspaceTypeRepository,
                 config: AppConfig
                 ):
        self._source_repository = source_repository
        self._workspace_type_repository = workspace_type_repository
        self.config = config

    def get_available_sources_by_type(self, type_id: UUID) -> SourceTypeOutputModel:
        """
        Get available sources by type
        """
        try:
            workspace_type_data = self._workspace_type_repository.get_workspace_type_per_id(type_id)
            if workspace_type_data:
                return SourceTypeOutputModel(
                    data=[SourceTypeModel.from_orm(workspace_type) for workspace_type in
                          self._source_repository.get_sources_by_type(workspace_type_data.name)])
            logger.error("Workspace type not found")
            raise WorkspaceTypeNotFound
        except DatabaseConnectionError:
            logger.error(f'Failed to get list of sources due to database issue')
            raise SourceTypeFetchDataError(message='Unable to get list of source types')

    def get_source_type_by_id(self, source_type_id: UUID) -> SourceTypeModel:
        """
        Get source type by id
        """
        try:
            return SourceTypeModel.from_orm(self._source_repository.get_source_type_by_id(source_type_id))
        except DatabaseConnectionError:
            logger.error("error when getting a source type by id")
            raise SourceTypeFetchDataError(message='Unable to get source type')
        except ValidationError:
            logger.error("error validating result")
            raise GenericValidationError("Source")

    async def add_source(self, source: NewSourceSchema) -> NewSourceOutput:
        """
        add a source to db

        Args:
            source: the source to add

        Returns:
            NewSourceOutput: the added source.
        """
        try:
            return NewSourceOutput.from_orm(await self._source_repository.add_source(source))
        except DatabaseConnectionError:
            logger.error("error adding a source")
            raise SourceAddingError(message='Unable to add source, database error')
        except ValidationError:
            logger.error("error validating result")
            raise GenericValidationError(model_name="NewSourceSchema")

    async def get_source_by_id(self, source_id: UUID) -> NewSourceOutput:
        """
        gets a source by id

         Args:
            source_id: the source id to get

        Returns:
            NewSourceOutput: the fetched source.
        """
        try:
            return NewSourceOutput.from_orm(await self._source_repository.get_source_by_id(source_id))
        except DatabaseConnectionError as database_error:
            logger.error(f"error getting source: {database_error.message}")
            raise SourceDataFetchError('Unable to get source, database error')
        except ValidationError:
            logger.error("error validating result")
            raise GenericValidationError("Source")

    async def get_source_by_workspace_id(self, workspace_id: UUID) -> NewSourceOutput:
        """
            gets a source by workspace id

             Args:
                workspace_id: the workspace id to use

            Returns:
                NewSourceOutput: the fetched source.
        """
        try:
            return NewSourceOutput.from_orm(await self._source_repository.get_source_by_workspace_id(workspace_id))
        except DatabaseConnectionError as database_error:
            logger.error(f"error getting source: {database_error.message}")
            raise SourceDataFetchError('Unable to get source, database error')
        except ValidationError:
            logger.error("error validating result")
            raise GenericValidationError(model_name="Source")

    async def update_source(self, source: NewSourceOutput) -> NewSourceOutput:
        """
            updates a source

             Args:
                source: NewSourceOutput - the source to update

            Returns:
                NewSourceOutput: the fetched source.
        """
        try:
            return await self._source_repository.update_source(source)
        except (DatabaseConnectionError, NoResultFound):
            logger.error("error updating  a source")
            raise SourceUpdatingError(message='Unable to update source, database error')
        except ValidationError:
            logger.error("error validating result")
            raise GenericValidationError(model_name="Source")

    async def get_source_ddl(self, workspace_id: UUID) -> SourceDDLOutputDTO:
        try:
            new_source_output: NewSourceOutput = await self.get_source_by_workspace_id(workspace_id=workspace_id)
            source_output: SourceOutputModel = SourceOutputModel(**new_source_output.dict())

            source_dict = await make_request(service_url=self.config.source_service_url,
                                             uri="/sources/metadata",
                                             body=jsonable_encoder(source_output),
                                             method=RequestMethod.POST)
            return SourceDDLOutputDTO(**source_dict)
        except (AttributeError, TypeError) as error:
            logger.error(error)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    async def execute_sql_command(self, workspace_id: UUID, sql_query: str) -> SqlExecuteResponse:
        """
        This function calls the `/query` API endpoint in the source service in order to execute
        the given SQL DQL command on the provided database URL. It returns the result of the command
        execution.
        :param workspace_id: Will be used to fetch the related database URL on which the command is to be executed.
        :param sql_query: The DQL command to be executed.
        :param query_depth: The query depth
        :return: Results of the command execution.
        """
        if not is_select_query(sql_query):
            raise UnauthorizedSQLStatement(
                "Execution of this query is not permitted, Only SELECT statements are allowed")
        try:
            new_source_output: NewSourceOutput = await self.get_source_by_workspace_id(workspace_id=workspace_id)
            logger.info({"source": new_source_output})
            source_output: SourceOutputModel = SourceOutputModel(**new_source_output.dict())
            logger.info({"source_output": source_output})
            logger.info({"query": sql_query})
            new_sql_execute_request: SqlExecuteRequest = SqlExecuteRequest(
                url=source_output.url,
                query=sql_query
            )

            sql_result = await make_request(service_url=self.config.source_service_url,
                                            uri="/sources/query",
                                            body=jsonable_encoder(new_sql_execute_request.dict()),
                                            method=RequestMethod.POST)
            return SqlExecuteResponse(**sql_result)
        except (TypeError, ValidationError) as error:
            logger.error(error)
            raise QueryExecutionFail
