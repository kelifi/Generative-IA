from uuid import UUID

from sqlalchemy import Row, desc
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseConnectionError, WorkspaceAlreadyExist, WorkspaceNotFoundError, \
    DuplicateAssignmentError
from source.helpers.db_helpers import DBHelper
from source.models.workspace_models import Workspace, UsersWorkspaces
from source.schemas.workspace_schema import WorkspaceOutput


class WorkspaceRepository:

    def __init__(self, database_helper: DBHelper):
        self.database_helper = database_helper

    def get_workspaces_by_user(self, user_id: UUID) -> list[Row]:
        """For a certain user id, return the list of all workspaces for that user"""
        with self.database_helper.session() as session:
            try:
                return session.query(Workspace).join(UsersWorkspaces,
                                                     Workspace.id == UsersWorkspaces.workspace_id).filter(
                    UsersWorkspaces.user_id == user_id, Workspace.active == True
                ).order_by(desc(Workspace.creation_date)).all()
            except SQLAlchemyError as error:
                logger.error(f'A data error happened on get workspace by user-id {error}')
                raise DatabaseConnectionError(f"Database connection error: {error}")

    def get_workspace_users(self, workspace_id: UUID) -> list[Row]:
        """ Get all users ids for a specific workspace"""
        with self.database_helper.session() as session:
            try:
                return session.query(UsersWorkspaces).join(Workspace,
                                                           Workspace.id == UsersWorkspaces.workspace_id).filter(
                    Workspace.id == workspace_id, Workspace.active == True).distinct().all()
            except SQLAlchemyError as error:
                logger.error(f'A data error happened on get workspace by user-id {error}')
                raise DatabaseConnectionError(f"Database connection error: {error}")

    def get_all_workspaces(self) -> list[Row]:
        """
        Retrieve a list of all workspaces from the database.

        Returns:
            list[Row]: A list of `Row` objects representing the retrieved workspaces.

        Raises:
            DatabaseConnectionError: If there is a database connection error during the retrieval.
        """
        with self.database_helper.session() as session:
            try:
                return session.query(Workspace).all()
            except SQLAlchemyError as error:
                logger.error(f'A data error happened on get workspace by user-id {error}')
                raise DatabaseConnectionError(f"Database connection error: {error}")

    def create_workspace(self, workspace_data: Workspace) -> WorkspaceOutput:
        """
        create a workspace
        :param workspace_data: data related to the workspace
        :return: uuid of the workspace
        """
        with self.database_helper.session() as session:
            try:
                if session.query(Workspace).filter_by(name=workspace_data.name).first():
                    logger.info(f"workspace with same name {workspace_data.name} already exist")
                    raise WorkspaceAlreadyExist
                session.add(workspace_data)
                session.commit()
                return WorkspaceOutput(
                    id=str(workspace_data.id),
                    name=workspace_data.name,
                    active=workspace_data.active,
                    description=workspace_data.description
                )
            except (SQLAlchemyError, DataError) as sql_alchemy_error:
                logger.error(f"Error saving workspace {sql_alchemy_error}")
                session.rollback()
                raise DatabaseConnectionError(f"Database error: {str(sql_alchemy_error)}")

    def assign_users_to_workspace(self, workspace_id: UUID, users_ids: list[UUID]) -> bool:
        """
        assign a user to a workspace
        :param workspace_id
        :param users_ids
        :return: uuid of the workspace
        """
        with self.database_helper.session() as session:
            try:
                if workspace := session.query(Workspace).get(workspace_id):
                    for user_id in users_ids:
                        assignment = UsersWorkspaces()
                        assignment.user_id = user_id
                        assignment.workspace_id = workspace.id
                        session.add(assignment)
                    session.commit()
                    return True
                raise WorkspaceNotFoundError(message=f"Workspace with ID {workspace_id} not found.")
            except IntegrityError as error:
                logger.error(f'An integrity error occurred: {error}')
                session.rollback()
                raise DuplicateAssignmentError('Duplicate assignment detected for user and workspace.')

            except (SQLAlchemyError, DataError) as error:
                logger.error(f'A data error happened on get workspace by user-id {error}')
                session.rollback()
                raise DatabaseConnectionError(f"Database connection error: {error}")
