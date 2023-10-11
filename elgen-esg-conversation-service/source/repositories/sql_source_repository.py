from sqlalchemy.exc import SQLAlchemyError

from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseConnectionError
from source.helpers.db_helpers import DBHelper
from source.models.conversations_models import SqlSourceResponse
from source.schemas.sql_llm_schema import SqlSourceResponseDTO


class SQLSourceRepository:
    def __init__(self, database_helper: DBHelper) -> None:
        self.__database_helper = database_helper

    def create_sql_source_response(self, data: SqlSourceResponse) -> SqlSourceResponseDTO:
        with self.__database_helper.session() as session:
            try:
                session.add(data)
                session.commit()
                session.refresh(data)

                return SqlSourceResponseDTO.from_orm(data)
            except SQLAlchemyError as sql_alchemy_error:
                logger.error(f"Error saving workspace {sql_alchemy_error}")
                session.rollback()
                raise DatabaseConnectionError(
                    f"Database error: {str(sql_alchemy_error)}"
                ) from sql_alchemy_error


