from uuid import UUID

from sqlalchemy import asc, Row
from sqlalchemy.exc import SQLAlchemyError

from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseConnectionError, WorkspaceTypeAlreadyExist
from source.helpers.db_helpers import DBHelper
from source.models.workspace_models import WorkspaceType
from source.schemas.workspace_schema import WorkspaceTypeModel


class WorkspaceTypeRepository:

    def __init__(self, database_helper: DBHelper):
        self.database_helper = database_helper

    def get_workspace_types(self) -> list[Row]:
        """
        Get list of available workspace types
        """
        try:
            with self.database_helper.session() as session:
                return session.query(WorkspaceType).filter(
                    WorkspaceType.available == True).order_by(asc(WorkspaceType.name)).all()
        except SQLAlchemyError as error:
            logger.error(f'An error happened when getting workspace types {error}')
            raise DatabaseConnectionError(f"Cannot get list of workspace types: {error}")

    def create_workspace_type(self, workspace_type_data: WorkspaceTypeModel) -> UUID:
        """
        Create new workspace type
        """
        try:
            with self.database_helper.session() as session:
                if session.query(WorkspaceType).filter_by(name=workspace_type_data.name).first():
                    logger.info(f"workspace with same name {workspace_type_data.name} already exist")
                    raise WorkspaceTypeAlreadyExist
                workspace_type = WorkspaceType()
                workspace_type.name = workspace_type_data.name
                workspace_type.description = workspace_type_data.description
                workspace_type.available = workspace_type_data.available
                session.add(workspace_type)
                session.commit()
                return workspace_type.id
        except SQLAlchemyError as error:
            logger.error(f'An error happened when creating workspace type {error}')
            raise DatabaseConnectionError(f"Cannot create new workspace type: {error}")

    def get_workspace_type_per_id(self, workspace_type_id: UUID) -> WorkspaceType:
        """
        Get workspace type per id
        """
        try:
            with self.database_helper.session() as session:
                return session.query(WorkspaceType).filter(WorkspaceType.id == workspace_type_id,
                                                           WorkspaceType.available == True).first()
        except SQLAlchemyError as error:
            logger.error(f'An error happened when getting workspace type {error}')
            raise DatabaseConnectionError(f"Cannot get workspace type: {error}")
