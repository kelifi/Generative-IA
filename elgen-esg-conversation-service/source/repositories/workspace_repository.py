from datetime import datetime
from uuid import UUID

from sqlalchemy import Row, desc
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError, NoResultFound

from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseConnectionError, WorkspaceAlreadyExist, WorkspaceNotFoundError, \
    DuplicateAssignmentError
from source.helpers.db_helpers import DBHelper
from source.models.workspace_models import Workspace, UsersWorkspaces
from source.schemas.workspace_schema import WorkspaceOutput, WorkspaceDto


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
                return session.query(Workspace).filter(Workspace.active == True).order_by(
                    desc(Workspace.creation_date)).all()
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
                if session.query(Workspace).filter_by(name=workspace_data.name, active=True, deleted=False).first():
                    logger.info(f"workspace with same name {workspace_data.name} already exist")
                    raise WorkspaceAlreadyExist
                session.add(workspace_data)
                session.commit()
                return WorkspaceOutput(
                    id=workspace_data.id,
                    name=workspace_data.name,
                    active=workspace_data.active,
                    description=workspace_data.description
                )
            except (SQLAlchemyError, DataError) as sql_alchemy_error:
                logger.error(f"Error saving workspace {sql_alchemy_error}")
                session.rollback()
                raise DatabaseConnectionError(f"Database error: {str(sql_alchemy_error)}")

    async def update_workspace(self, workspace_data: WorkspaceDto, workspace_id: UUID) -> bool:
        """
        Update workspace data by id
        """
        with self.database_helper.session() as session:
            if workspace_to_update := session.query(Workspace).get(workspace_id):
                logger.info(f"Updating workspace with id {workspace_id}")
                for field, value in workspace_data.dict(exclude_unset=True, exclude_none=True).items():
                    if field == "available_model_codes":
                        value = ",".join(value)
                    setattr(workspace_to_update, field, value)
                try:
                    session.commit()
                except DataError as ex:
                    session.rollback()
                    logger.error(f'A data error happened on update workspace  {ex}')
                    raise DatabaseConnectionError(f'Cannot update workspace {ex}')
                except SQLAlchemyError as ex:
                    logger.error(f'An error happened on update workspace {ex}')
                    raise DatabaseConnectionError(f'Cannot update workspace {ex}')
                session.refresh(workspace_to_update)
                return True
            raise NoResultFound

    async def delete_workspace(self, workspace_id: UUID) -> bool:
        """Delete a workspace based on its id"""
        with self.database_helper.session() as session:
            if workspace := session.query(Workspace).get(workspace_id):
                workspace.active = False
                workspace.deleted = True
                workspace.update_date = datetime.now()
                logger.info(f"Delete workspace with id {workspace_id}")
                try:
                    session.commit()
                except DataError as ex:
                    session.rollback()
                    logger.error(f'A data error happened on delete workspace {ex}')
                    raise DatabaseConnectionError(f'Cannot delete workspace {ex}')
                except SQLAlchemyError as ex:
                    logger.error(f'An error happened on delete workspace {ex}')
                    raise DatabaseConnectionError(f'Cannot create source documents {ex}')
                session.refresh(workspace)
                return True
            raise NoResultFound

    def get_workspace_by_id(self, workspace_id: UUID):
        """
        Get workspace by workspace id
        """
        try:
            with self.database_helper.session() as session:
                return session.query(Workspace).filter(
                    Workspace.id == workspace_id).first()
        except SQLAlchemyError as error:
            logger.error(f'An error happened when getting workspace {error}')
            raise DatabaseConnectionError(f"Cannot get workspace: {error}")

    def assign_users_to_workspace(self, workspace_id: UUID, users_ids: list[str]) -> bool:
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

    def get_workspace_type(self, workspace_id):
        """
        get workspace type
        :param workspace_id
        :return: workspace type
        """
        with self.database_helper.session() as session:
            try:
                return session.query(Workspace).filter_by(id=workspace_id).first().type
            except AttributeError as error:
                logger.error(f'Couldn\'t find workspace type for workspace with id {workspace_id}: {error}')
                raise DatabaseConnectionError(f"Database connection error: {error}")
            except SQLAlchemyError as error:
                logger.error(f'A data error happened on get workspace byid {error}')
                raise DatabaseConnectionError(f"Database connection error: {error}")
