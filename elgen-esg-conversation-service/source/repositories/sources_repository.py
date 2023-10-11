from uuid import UUID

from sqlalchemy import Row
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound, DataError

from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseConnectionError, DatabaseIntegrityError
from source.helpers.db_helpers import DBHelper
from source.models.source_models import SourceType, Source
from source.schemas.source_schema import NewSourceSchema, NewSourceOutput


class SourceRepository:

    def __init__(self, database_helper: DBHelper):
        self.database_helper = database_helper

    def get_sources_by_type(self, type_name: str) -> list[Row]:
        """
        Get list of available workspace types
        """
        try:
            with self.database_helper.session() as session:
                return session.query(SourceType).filter(
                    SourceType.type_name == type_name,
                    SourceType.available == True,
                ).all()
        except SQLAlchemyError as error:
            logger.error(f'An error happened when getting workspace types {error}')
            raise DatabaseConnectionError(f"Cannot get list of workspace types: {error}")

    def get_source_type_by_id(self, source_type_id: UUID) -> Row:
        """
        Get source type per id
        """
        try:
            with self.database_helper.session() as session:
                return session.query(SourceType).filter(SourceType.id == source_type_id,
                                                        SourceType.available == True).first()
        except SQLAlchemyError as error:
            logger.error(f'An error happened when getting source type {error}')
            raise DatabaseConnectionError(f"Cannot get source type: {error}")

    async def add_source(self, new_source: NewSourceSchema) -> Source:
        """adds a source to db"""
        source = Source(**new_source.dict())
        with self.database_helper.session() as session:
            session.add(source)
            try:
                session.commit()
            except IntegrityError as error:
                session.rollback()
                logger.error(error)
                raise DatabaseIntegrityError(
                    message='An integrity error happened when creating new Source')
            except SQLAlchemyError as error:
                session.rollback()
                logger.error(error)
                raise DatabaseConnectionError(message='Cannot add source')
            session.refresh(source)
            return source

    async def get_source_by_id(self, source_id: UUID) -> Row:
        """
        Retrieve a source by id.

        Returns:
            Row: A `Row` objects representing the retrieved Source.

        Raises:
            DatabaseConnectionError: If there is a database connection error during the retrieval.
        """
        with self.database_helper.session() as session:
            try:
                return session.query(Source).filter(Source.id == source_id).first()
            except SQLAlchemyError as error:
                logger.error(f'A data error happened on get workspace by user-id {error}')
                raise DatabaseConnectionError(f"Database connection error: {error}")

    async def get_source_by_workspace_id(self, workspace_id: UUID) -> Row:
        """
        Retrieve a source by workspace id.

        Returns:
            Row: A  `Row` objects representing the retrieved Source.

        Raises:
            DatabaseConnectionError: If there is a database connection error during the retrieval.
        """
        with self.database_helper.session() as session:
            try:
                return session.query(Source).filter(Source.workspace_id == workspace_id).first()
            except SQLAlchemyError as error:
                logger.error(f'A data error happened on get workspace by user-id {error}')
                raise DatabaseConnectionError(f"Database connection error: {error}")

    async def update_source(self, source: NewSourceOutput) -> NewSourceOutput:
        """Update a source"""
        with self.database_helper.session() as session:
            if source_to_update := session.query(Source).get(source.id):
                logger.info(f"Updating source with id {source.id}")
                for field, value in source.dict(exclude_unset=True).items():
                    setattr(source_to_update, field, value)
                try:
                    session.commit()
                except DataError as ex:
                    session.rollback()
                    logger.error(f'A data error happened on update source {ex}')
                    raise DatabaseConnectionError(f'Cannot update source {ex}')
                except SQLAlchemyError as ex:
                    logger.error(f'An error happened on update source {ex}')
                    raise DatabaseConnectionError(f'Cannot update source {ex}')
                session.refresh(source_to_update)
                return NewSourceOutput.from_orm(source_to_update)
            raise NoResultFound
